import io

import pandas as pd
import pytest


def test_loader_uses_semicolon_and_preserves_accents():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    assert len(frame) == 360
    assert 'Saída' in set(frame['tipo'].unique())
    assert str(frame['data_prevista'].min())[:10] == '2025-10-06'
    assert str(frame['data_prevista'].max())[:10] == '2026-09-30'


def test_signed_value_uses_tipo_for_sign():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    frame = data_module.with_signed_value(frame)
    outflows = frame[frame['tipo'] == 'Saída']['signed_value']
    inflows = frame[frame['tipo'] == 'Entrada']['signed_value']
    assert (outflows < 0).all()
    assert (inflows > 0).all()


def test_filter_by_tipo_and_status():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    filtered = data_module.filter_cashflow(frame, tipos=['Entrada'])
    assert (filtered['tipo'] == 'Entrada').all()
    realized = data_module.filter_cashflow(
        frame, statuses=['Pago', 'Recebido']
    )
    assert set(realized['status'].unique()) <= {'Pago', 'Recebido'}


def test_filter_empty_list_returns_empty():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    assert data_module.filter_cashflow(frame, tipos=[]).empty
    assert data_module.filter_cashflow(frame, categorias=[]).empty
    assert data_module.filter_cashflow(frame, cost_centers=[]).empty
    assert data_module.filter_cashflow(frame, statuses=[]).empty
    assert data_module.filter_cashflow(frame, recurring=[]).empty


def test_filter_none_returns_all():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    filtered = data_module.filter_cashflow(frame)
    assert len(filtered) == len(frame)


def test_filter_window_uses_only_data_prevista():
    from cashflow import data as data_module

    df = pd.DataFrame(
        {
            'tipo': ['Entrada', 'Saída'],
            'categoria': ['Vendas', 'Adm'],
            'centro_custo': ['Comercial', 'Administrativo'],
            'status': ['Pago', 'Pago'],
            'recorrente': ['Não', 'Sim'],
            'data_prevista': pd.to_datetime(['2026-01-15', '2026-02-15']),
            'data_realizada': pd.to_datetime(['2025-01-01', '2026-01-15']),
            'valor': [100.0, 50.0],
        }
    )
    filtered = data_module.filter_cashflow(
        df, start='2026-01-01', end='2026-01-31'
    )
    assert len(filtered) == 1
    assert filtered.iloc[0]['tipo'] == 'Entrada'


def test_window_anchor_last_days():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    end = frame['data_prevista'].max()
    # Não assumir 1 linha/dia: dataset futuro pode ter múltiplas
    # linhas por dia; janela cobre >= days linhas dentro do intervalo.
    for days in [30, 360]:
        start = end - pd.Timedelta(days=days - 1)
        windowed = data_module.filter_cashflow(frame, start=start, end=end)
        assert len(windowed) >= days
        assert (windowed['data_prevista'] >= start).all()
        assert (windowed['data_prevista'] <= end).all()


def test_with_signed_value_rejects_unknown_tipo():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = 'Foo'
    with pytest.raises(ValueError):
        data_module.with_signed_value(frame)


def test_with_signed_value_rejects_nan_tipo():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = None
    with pytest.raises(ValueError):
        data_module.with_signed_value(frame)


def test_load_cashflow_missing_file():
    from cashflow import data as data_module

    with pytest.raises(FileNotFoundError):
        data_module.load_cashflow('data/nao_existe.csv')


def test_load_cashflow_requires_columns(tmp_path):
    from cashflow import data as data_module

    bad = tmp_path / 'bad.csv'
    bad.write_text('a;b\n1;2\n', encoding='utf-8')
    with pytest.raises(ValueError):
        data_module.load_cashflow(str(bad))


def test_previsto_rows_have_nat_data_realizada():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    previsto = frame[frame['status'] == 'Previsto']
    assert len(previsto) > 0
    assert previsto['data_realizada'].isna().all()


def test_export_sep_roundtrip():
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    filtered = data_module.filter_cashflow(frame, tipos=['Entrada']).head(5)
    payload = filtered.to_csv(index=False, sep=';', encoding='utf-8-sig').encode(
        'utf-8-sig'
    )
    assert b';' in payload
    back = pd.read_csv(io.BytesIO(payload), sep=';', encoding='utf-8-sig')
    assert len(back) == len(filtered)
    assert list(back.columns) == list(filtered.columns)


CSV_HEADER = (
    'id_lancamento;data_prevista;data_realizada;tipo;categoria;'
    'descricao;centro_custo;status;valor;recorrente'
)


def test_load_cashflow_latin1_raises_friendly(tmp_path):
    from cashflow import data as data_module

    row = (
        '1;2025-10-06;2025-10-06;Saída;Adm;Conta;Administrativo;'
        'Pago;100.0;Não\n'
    )
    target = tmp_path / 'latin1.csv'
    target.write_bytes((CSV_HEADER + '\n' + row).encode('latin1'))
    with pytest.raises(ValueError, match='utf-8'):
        data_module.load_cashflow(str(target))


def test_load_cashflow_invalid_valor_raises_contextual(tmp_path):
    from cashflow import data as data_module

    row = (
        '1;2025-10-06;2025-10-06;Entrada;Vendas;desc;Comercial;'
        'Pago;abc;Não\n'
    )
    target = tmp_path / 'bad_valor.csv'
    target.write_text(CSV_HEADER + '\n' + row, encoding='utf-8')
    with pytest.raises(ValueError, match='valor'):
        data_module.load_cashflow(str(target))


def test_load_cashflow_empty_raises(tmp_path):
    from cashflow import data as data_module

    target = tmp_path / 'empty.csv'
    target.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='vazio'):
        data_module.load_cashflow(str(target))


def test_load_cashflow_parser_error_raises(tmp_path, monkeypatch):
    from cashflow import data as data_module

    def _boom(*args, **kwargs):
        raise pd.errors.ParserError('boom sintético')

    monkeypatch.setattr(pd, 'read_csv', _boom)
    with pytest.raises(ValueError, match='parsear'):
        data_module.load_cashflow(str(tmp_path / 'x.csv'))


def test_with_signed_value_missing_tipo_raises_keyerror():
    from cashflow import data as data_module

    frame = pd.DataFrame({'valor': [10.0]})
    with pytest.raises(KeyError):
        data_module.with_signed_value(frame)


def test_with_signed_value_null_count_in_message():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = None
    with pytest.raises(ValueError, match='n_nulos=1'):
        data_module.with_signed_value(frame)


def test_with_signed_value_rejects_nan_valor():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'valor'] = float('nan')
    with pytest.raises(ValueError, match='valor'):
        data_module.with_signed_value(frame)


def test_group_daily_net_excludes_nat_data_prevista():
    from cashflow import data as data_module

    frame = pd.DataFrame(
        {
            'data_prevista': pd.to_datetime(['2026-01-01', None]),
            'signed_value': [100.0, 50.0],
        }
    )
    grouped = data_module.group_daily_net(frame)
    assert len(grouped) == 1
    assert float(grouped['net'].sum()) == pytest.approx(100.0)


def test_with_signed_value_rejects_negative_entrada():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = 'Entrada'
    frame.loc[frame.index[0], 'valor'] = -100.0
    with pytest.raises(ValueError, match='n_negativos'):
        data_module.with_signed_value(frame)


def test_with_signed_value_rejects_negative_saida():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = 'Saída'
    frame.loc[frame.index[0], 'valor'] = -100.0
    with pytest.raises(ValueError, match='n_negativos'):
        data_module.with_signed_value(frame)


def test_filter_cashflow_invalid_start_raises_friendly():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start='not-a-date')


def test_filter_cashflow_invalid_end_raises_friendly():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, end='not-a-date')


def test_load_cashflow_directory_raises_friendly(tmp_path):
    from cashflow import data as data_module

    with pytest.raises(ValueError, match='falha ao ler'):
        data_module.load_cashflow(str(tmp_path))


def test_filter_cashflow_rejects_empty_string_window():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start='')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, end='')


def test_filter_cashflow_rejects_nat_window():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start=pd.NaT)
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, end=pd.NaT)


def test_filter_cashflow_rejects_numeric_window():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start=12345)
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, end=12345)


def test_with_signed_value_rejects_zero_valor():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'tipo'] = 'Entrada'
    frame.loc[frame.index[0], 'valor'] = 0.0
    with pytest.raises(ValueError, match='valor'):
        data_module.with_signed_value(frame)


def test_with_signed_value_rejects_inf_valor():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame.loc[frame.index[0], 'valor'] = float('inf')
    with pytest.raises(ValueError, match='inf'):
        data_module.with_signed_value(frame)


def test_with_signed_value_missing_valor_raises_friendly():
    import pandas as pd

    from cashflow import data as data_module

    frame = pd.DataFrame({'tipo': ['Entrada']})
    with pytest.raises(ValueError, match='colunas ausentes'):
        data_module.with_signed_value(frame)


def test_with_signed_value_rejects_non_numeric_valor():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame = frame.astype({'valor': 'object'})
    frame.loc[frame.index[0], 'valor'] = 'abc'
    with pytest.raises(ValueError, match='não-numéricos'):
        data_module.with_signed_value(frame)


def test_filter_cashflow_rejects_list_window():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start=['2026-01-01'])


def test_filter_cashflow_rejects_tz_aware_window():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    tz_start = pd.Timestamp('2026-01-01', tz='UTC')
    tz_end = pd.Timestamp('2026-01-31', tz='UTC')
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start=tz_start)
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, end=tz_end)
    with pytest.raises(ValueError, match='janela inválida'):
        data_module.filter_cashflow(frame, start='2026-01-01T00:00:00+00:00')


def test_with_signed_value_rejects_string_numeric_valor():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv').head(3).copy()
    frame = frame.astype({'valor': 'object'})
    frame.loc[frame.index[0], 'valor'] = '100.0'
    with pytest.raises(ValueError, match='não-numéricos'):
        data_module.with_signed_value(frame)


def test_group_daily_net_missing_data_prevista_raises_friendly():
    from cashflow import data as data_module

    frame = pd.DataFrame({'signed_value': [100.0]})
    with pytest.raises(ValueError, match='colunas ausentes'):
        data_module.group_daily_net(frame)


def test_with_signed_value_rejects_bool_valor():
    from cashflow import data as data_module

    frame = pd.DataFrame(
        {'tipo': ['Entrada'], 'valor': pd.Series([True], dtype='bool')}
    )
    with pytest.raises(ValueError, match='bool'):
        data_module.with_signed_value(frame)


def test_public_validators_available_with_private_alias():
    from cashflow import data as data_module

    assert callable(data_module.require_columns)
    assert callable(data_module.validate_valor)
    assert data_module._require_columns is data_module.require_columns
    assert data_module._validate_valor is data_module.validate_valor


def test_filter_cashflow_window_missing_data_prevista_raises_friendly():
    import pandas as pd

    from cashflow import data as data_module

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada'],
            'categoria': ['Vendas'],
            'centro_custo': ['Comercial'],
            'status': ['Pago'],
            'recorrente': ['Não'],
            'valor': [100.0],
        }
    )
    with pytest.raises(ValueError, match='colunas ausentes'):
        data_module.filter_cashflow(frame, start='2026-01-01')
    with pytest.raises(ValueError, match='colunas ausentes'):
        data_module.filter_cashflow(frame, end='2026-01-31')
    with pytest.raises(ValueError, match='colunas ausentes'):
        data_module.filter_cashflow(
            frame, start='2026-01-01', end='2026-01-31'
        )
    # Sem janela: None retorna tudo mesmo sem data_prevista.
    assert len(data_module.filter_cashflow(frame)) == 1
    # Lista vazia mantém semântica empty.
    assert data_module.filter_cashflow(frame, tipos=[]).empty


def test_filter_missing_categorical_raises_friendly():
    import pandas as pd

    from cashflow import data as data_module

    base = {
        'tipo': ['Entrada'],
        'categoria': ['Vendas'],
        'centro_custo': ['Comercial'],
        'status': ['Pago'],
        'recorrente': ['Não'],
        'data_prevista': pd.to_datetime(['2026-01-15']),
        'valor': [100.0],
    }
    cases = [
        ('tipo', 'tipos', ['Entrada']),
        ('categoria', 'categorias', ['Vendas']),
        ('centro_custo', 'cost_centers', ['Comercial']),
        ('status', 'statuses', ['Pago']),
        ('recorrente', 'recurring', ['Não']),
    ]
    for missing_col, kwarg, values in cases:
        frame = pd.DataFrame(
            {k: v for k, v in base.items() if k != missing_col}
        )
        assert missing_col not in frame.columns
        with pytest.raises(ValueError, match='colunas ausentes'):
            data_module.filter_cashflow(frame, **{kwarg: values})


def test_filter_empty_list_preserves_empty_without_column():
    import pandas as pd

    from cashflow import data as data_module

    frame = pd.DataFrame({'valor': [100.0]})
    assert data_module.filter_cashflow(frame, tipos=[]).empty
    assert data_module.filter_cashflow(frame, categorias=[]).empty
    assert data_module.filter_cashflow(frame, cost_centers=[]).empty
    assert data_module.filter_cashflow(frame, statuses=[]).empty
    assert data_module.filter_cashflow(frame, recurring=[]).empty
    # None desliga o filtro: retorna tudo mesmo sem as colunas.
    assert len(data_module.filter_cashflow(frame)) == 1


def test_filter_start_after_end_returns_empty():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    filtered = data_module.filter_cashflow(
        frame, start='2026-02-01', end='2026-01-01'
    )
    assert filtered.empty


def test_filter_all_categoricals_success():
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    by_cat = data_module.filter_cashflow(frame, categorias=['Vendas'])
    assert not by_cat.empty
    assert (by_cat['categoria'] == 'Vendas').all()
    by_cc = data_module.filter_cashflow(frame, cost_centers=['Comercial'])
    assert not by_cc.empty
    assert (by_cc['centro_custo'] == 'Comercial').all()
    by_rec = data_module.filter_cashflow(frame, recurring=['Sim'])
    assert not by_rec.empty
    assert (by_rec['recorrente'] == 'Sim').all()
