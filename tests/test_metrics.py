import pytest


def test_summary_totals_match_sample():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    summary = metrics_module.build_summary(frame)
    assert summary['total_inflows'] == pytest.approx(2113072.23)
    assert summary['total_outflows'] == pytest.approx(1449988.59)
    assert summary['net_balance'] == pytest.approx(663083.64)


def test_summary_forecast_coverage():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    summary = metrics_module.build_summary(frame)
    assert summary['forecast_coverage'] == pytest.approx(1.41, rel=1e-2)
    assert summary['realized_share'] == pytest.approx(0.931, rel=1e-2)
