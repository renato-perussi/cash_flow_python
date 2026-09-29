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
    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f'colunas ausentes no CSV: {missing}')
    try:
        frame['data_prevista'] = pd.to_datetime(
            frame['data_prevista'], errors='coerce'
        )
        frame['data_realizada'] = pd.to_datetime(
            frame['data_realizada'], errors='coerce'
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"falha ao converter colunas de data ('data_prevista', "
            f"'data_realizada') arquivo: {path}: {exc}"
        ) from exc
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
    inclui n_nulos e valores inválidos). Validação estrita:
    NaN em ``valor`` também levanta ValueError (não propaga NaN
    para signed_value/métricas). Valor negativo também levanta
    ValueError: o contrato canônico exige ``valor`` > 0 e o sinal
    deriva de ``tipo`` (sem essa guarda, Entrada -100 geraria
    signed -100 e Saída -100 geraria +100 — inversão silenciosa).
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
    if 'valor' in frame.columns and frame['valor'].isna().any():
        n_nan = int(frame['valor'].isna().sum())
        raise ValueError(
            f"valores ausentes (NaN) em coluna 'valor': n_nulos={n_nan}"
        )
    if 'valor' in frame.columns and (frame['valor'] < 0).any():
        n_neg = int((frame['valor'] < 0).sum())
        raise ValueError(
            "valores negativos em coluna 'valor': "
            f'n_negativos={n_neg} (esperado valor>0; sinal deriva de '
            "'tipo')"
        )
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

    None desliga o filtro; lista vazia [] retorna vazio (isin([])).
    A janela filtra somente data_prevista, nunca data_realizada.
    Linhas com data_prevista NaT nunca passam na janela
    (comparação com NaT é False) e ficam fora do resultado.
    Janela inválida (start/end não parseável) levanta ValueError
    amigável com start/end e causa original preservada.
    """
    result = frame.copy()
    if tipos is not None:
        result = result[result['tipo'].isin(tipos)]
    if categorias is not None:
        result = result[result['categoria'].isin(categorias)]
    if cost_centers is not None:
        result = result[result['centro_custo'].isin(cost_centers)]
    if statuses is not None:
        result = result[result['status'].isin(statuses)]
    if recurring is not None:
        result = result[result['recorrente'].isin(recurring)]
    if start is not None:
        try:
            start_ts = pd.to_datetime(start)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f'janela inválida start={start!r} end={end!r}: '
                f'falha ao converter start: {exc}'
            ) from exc
        result = result[result['data_prevista'] >= start_ts]
    if end is not None:
        try:
            end_ts = pd.to_datetime(end)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f'janela inválida start={start!r} end={end!r}: '
                f'falha ao converter end: {exc}'
            ) from exc
        result = result[result['data_prevista'] <= end_ts]
    return result
