def test_charts_return_figures():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    assert charts_module.daily_net_flow(frame) is not None
    assert charts_module.cumulative_balance(frame) is not None
    assert charts_module.inflows_by_category(frame) is not None
    assert charts_module.outflows_by_cost_center(frame) is not None
    assert charts_module.realized_vs_forecast(frame) is not None
    assert charts_module.recurring_split(frame) is not None
