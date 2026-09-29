"""Carregamento e transformação do CSV de cash-flow (sep=";", pt-BR)."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'id_lancamento',
    'data_prevista',
    'data_realizada',
    'tipo',
    'categoria',
    'descricao',
    'centro_custo',
    'status',
    'valor',
    'recorrente',
]

VALID_TIPOS = frozenset({'Entrada', 'Saída'})

SIGNED_VALUE_GUARD_MSG = 'chame with_signed_value antes'


def require_columns(frame, required, contexto):
    """Valida presença de colunas; levanta ValueError amigável."""
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f'colunas ausentes {contexto}: {missing}')


_require_columns = require_columns


def validate_valor(frame):
    """Valida coluna ``valor``: sem NaN, finita e > 0.

    Mensagens incluem contadores (n_nulos/n_inf/n_negativos/n_zeros)
    para diagnóstico. Ausência da coluna é tolerada aqui — a falha
    posterior é ValueError amigável via require_columns em
    with_signed_value. Dtype bool ou
    não-numérico (object/str, ex. '100.0') é rejeitado com ValueError,
    pois ``np.where`` quebraria com TypeError silencioso no pipeline.
    """
    if 'valor' not in frame.columns:
        return
    if pd.api.types.is_bool_dtype(frame['valor']):
        raise ValueError(
            "coluna 'valor' com dtype bool inválida "
            f'(dtype={frame["valor"].dtype}; esperado numérico >0)'
        )
    n_nulos = int(frame['valor'].isna().sum())
    if n_nulos:
        raise ValueError(
            f"valores ausentes (NaN) em coluna 'valor': n_nulos={n_nulos}"
        )
    try:
        arr = frame['valor'].to_numpy(dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"valores não-numéricos em coluna 'valor': {exc}"
        ) from exc
    if not pd.api.types.is_numeric_dtype(frame['valor']):
        raise ValueError(
            'valores não-numéricos em coluna '
            f"'valor': dtype={frame['valor'].dtype} "
            '(esperado numérico >0; string-numérico como '
            "'100.0' não é aceito)"
        )
    n_inf = int((~np.isfinite(arr)).sum())
    if n_inf:
        raise ValueError(
            "valores não-finitos (inf) em coluna 'valor': "
            f'n_inf={n_inf} (esperado valor finito >0)'
        )
    n_neg = int((arr < 0).sum())
    n_zero = int((arr == 0).sum())
    if n_neg or n_zero:
        raise ValueError(
            "valores não-positivos em coluna 'valor': "
            f'n_negativos={n_neg} n_zeros={n_zero} '
            "(esperado valor>0; sinal deriva de 'tipo')"
        )


_validate_valor = validate_valor


def _parse_window_bound(value, *, name, start, end):
    """Converte bound de janela (start/end) para Timestamp.

    Rejeita ''/branco, NaT/None/NaN, numéricos (int/float — o pandas
    interpretaria 12345 como nanos desde epoch, janela silenciosa
    errada), tz-aware (comparação naive vs aware quebraria o filtro
    com TypeError) e sequências; NaT resultante também rejeitado.
    ValueError (não TypeError) de propósito: contrato de
    filter_cashflow é sempre ValueError 'janela inválida'.
    """
    if isinstance(value, (bool, int, float, np.integer, np.floating)):
        raise ValueError(  # noqa: TRY004 - contrato exige ValueError
            f'janela inválida start={start!r} end={end!r}: '
            f'{name} deve ser data/str, recebido '
            f'{type(value).__name__} {value!r}'
        )
    if isinstance(value, str) and value.strip() == '':
        raise ValueError(
            f'janela inválida start={start!r} end={end!r}: {name} vazio'
        )
    try:
        parsed = pd.to_datetime(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(
            f'janela inválida start={start!r} end={end!r}: '
            f'falha ao converter {name}: {exc}'
        ) from exc
    if isinstance(parsed, (pd.DatetimeIndex, pd.Series, np.ndarray, list)):
        raise ValueError(  # noqa: TRY004 - contrato exige ValueError
            f'janela inválida start={start!r} end={end!r}: '
            f'{name} deve ser escalar, recebido {value!r}'
        )
    if pd.isna(parsed):
        raise ValueError(
            f'janela inválida start={start!r} end={end!r}: '
            f'{name} resultou NaT ({value!r})'
        )
    if isinstance(parsed, pd.Timestamp) and parsed.tz is not None:
        raise ValueError(
            f'janela inválida start={start!r} end={end!r}: '
            f'{name} tz-aware rejeitado ({value!r}); '
            'use data naive sem timezone'
        )
    return parsed


def load_cashflow(path):
    """Carrega o CSV canônico de cash-flow.

    Usa sep=";" e encoding utf-8-sig (lê utf-8 com ou sem BOM).
    Valida colunas requeridas e faz parse de datas com
    errors="coerce" (NaT em data_realizada de linhas Previsto é
    esperado, não dado faltante).

    Erros de encoding (ex.: arquivo latin1 de Excel pt-BR) e de
    conversão da coluna ``valor`` levantam ValueError contextual
    com o caminho do arquivo.
    """
    try:
        frame = pd.read_csv(path, sep=';', encoding='utf-8-sig')
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f'arquivo de cash flow não encontrado: {path}'
        ) from exc
    except OSError as exc:
        raise ValueError(
            f'falha ao ler arquivo de cash flow: {path}: {exc}'
        ) from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            f'falha ao parsear CSV de cash flow: {path}: {exc}'
        ) from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f'CSV de cash flow vazio ou sem header: {path}: {exc}'
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            f'encoding esperado utf-8 (utf-8-sig), falha ao decodificar '
            f'arquivo: {path}: {exc}'
        ) from exc
    _require_columns(frame, REQUIRED_COLUMNS, 'no CSV')
    # errors="coerce": nunca levanta — inválidas viram NaT. NaT em
    # data_realizada de linhas Previsto é esperado, não dado faltante;
    # NaT em data_prevista é excluído com warning em group_daily_net
    # e build_summary (invariante summary==daily).
    frame['data_prevista'] = pd.to_datetime(
        frame['data_prevista'], errors='coerce'
    )
    frame['data_realizada'] = pd.to_datetime(
        frame['data_realizada'], errors='coerce'
    )
    try:
        frame['valor'] = frame['valor'].astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"falha ao converter coluna 'valor' para float arquivo: "
            f'{path}: {exc}'
        ) from exc
    return frame


def with_signed_value(frame):
    """Adiciona coluna signed_value (+Entrada / -Saída).

    Vetorizado com np.where. Valida tipo em {Entrada, Saída} e
    levanta ValueError para tipo desconhecido ou NaN (mensagem
    inclui n_nulos e valores inválidos). Validação estrita via
    validate_valor: NaN/inf/0/negativo/bool/dtype não-numérico
    levantam ValueError (não propagam NaN/inf para
    signed_value/métricas). O contrato canônico exige ``valor``
    finito > 0 e o sinal deriva de ``tipo`` (sem essa guarda,
    Entrada -100 geraria signed -100 e Saída -100 geraria +100 —
    inversão silenciosa). Coluna ``valor`` ausente levanta
    ValueError amigável (colunas ausentes em with_signed_value);
    coluna ``tipo`` ausente mantém KeyError histórico (get_frame
    trata ValueError e KeyError).
    """
    if 'tipo' not in frame.columns:
        raise KeyError("coluna 'tipo' ausente; verifique load_cashflow")
    invalid = ~frame['tipo'].isin(VALID_TIPOS)
    if invalid.any():
        bad = sorted(frame.loc[invalid, 'tipo'].dropna().unique().tolist())
        n_nulls = int(frame['tipo'].isna().sum())
        raise ValueError(
            f'tipos inválidos em coluna tipo: {bad} (n_nulos={n_nulls})'
        )
    _validate_valor(frame)
    require_columns(frame, ['valor'], 'em with_signed_value')
    result = frame.copy()
    result['signed_value'] = np.where(
        result['tipo'] == 'Entrada', result['valor'], -result['valor']
    )
    return result


def require_signed_value(frame):
    """Garante que signed_value existe; senão orienta a ordem correta."""
    if 'signed_value' not in frame.columns:
        raise KeyError(SIGNED_VALUE_GUARD_MSG)


def group_daily_net(frame):
    """Agrupa fluxo líquido diário por data_prevista (requer signed_value).

    Linhas com data_prevista NaT (coerce em load_cashflow) são
    excluídas explicitamente via dropna antes do groupby — o groupby
    pandas ignora NaT silenciosamente, então sem o drop a soma de
    `net` divergiria da soma de `signed_value` sem aviso.
    """
    require_signed_value(frame)
    require_columns(frame, ['data_prevista'], 'em group_daily_net')
    n_nat = int(frame['data_prevista'].isna().sum())
    if n_nat:
        logger.warning(
            'group_daily_net: excluindo %d linha(s) com data_prevista NaT',
            n_nat,
        )
        frame = frame.dropna(subset=['data_prevista'])
    grouped = frame.groupby('data_prevista', as_index=False).agg(
        net=('signed_value', 'sum')
    )
    return grouped.sort_values('data_prevista')


def filter_cashflow(
    frame,
    tipos=None,
    categorias=None,
    cost_centers=None,
    statuses=None,
    recurring=None,
    start=None,
    end=None,
):
    """Filtra por listas inclusivas e janela de data_prevista.

    None desliga o filtro; lista vazia [] retorna vazio sem exigir
    a coluna (head(0) preserva empty mesmo sem a coluna).
    Lista não-vazia exige a coluna correspondente (LOW-04):
    filtro ativo sobre coluna ausente levanta ValueError amigável
    via require_columns em filter_cashflow (não KeyError bruto),
    compatível com o except ValueError em app.py.
    A janela filtra somente data_prevista, nunca data_realizada.
    Linhas com data_prevista NaT nunca passam na janela
    (comparação com NaT é False) e ficam fora do resultado.
    Janela inválida (''/NaT/numérico/não parseável) levanta
    ValueError amigável com start/end e causa original preservada
    via _parse_window_bound. Janela com start/end exige coluna
    data_prevista (ValueError colunas ausentes em filter_cashflow);
    sem janela, None retorna tudo mesmo sem a coluna.
    start>end retorna vazio por design (INFO-03): sem exceção,
    pois nenhuma data_prevista satisfaz ambas as condições.
    """
    result = frame.copy()
    if tipos is not None:
        if len(tipos) == 0:
            result = result.head(0)
        else:
            require_columns(frame, ['tipo'], 'em filter_cashflow')
            result = result[result['tipo'].isin(tipos)]
    if categorias is not None:
        if len(categorias) == 0:
            result = result.head(0)
        else:
            require_columns(frame, ['categoria'], 'em filter_cashflow')
            result = result[result['categoria'].isin(categorias)]
    if cost_centers is not None:
        if len(cost_centers) == 0:
            result = result.head(0)
        else:
            require_columns(frame, ['centro_custo'], 'em filter_cashflow')
            result = result[result['centro_custo'].isin(cost_centers)]
    if statuses is not None:
        if len(statuses) == 0:
            result = result.head(0)
        else:
            require_columns(frame, ['status'], 'em filter_cashflow')
            result = result[result['status'].isin(statuses)]
    if recurring is not None:
        if len(recurring) == 0:
            result = result.head(0)
        else:
            require_columns(frame, ['recorrente'], 'em filter_cashflow')
            result = result[result['recorrente'].isin(recurring)]
    if start is not None or end is not None:
        require_columns(frame, ['data_prevista'], 'em filter_cashflow')
    if start is not None:
        start_ts = _parse_window_bound(
            start, name='start', start=start, end=end
        )
        result = result[result['data_prevista'] >= start_ts]
    if end is not None:
        end_ts = _parse_window_bound(end, name='end', start=start, end=end)
        result = result[result['data_prevista'] <= end_ts]
    return result
