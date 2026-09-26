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
