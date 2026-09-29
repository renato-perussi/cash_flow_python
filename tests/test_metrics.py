import math

import pandas as pd
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


def test_summary_totals_relative():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    summary = metrics_module.build_summary(frame)
    expected_in = frame.loc[frame['tipo'] == 'Entrada', 'valor'].sum()
    expected_out = frame.loc[frame['tipo'] == 'Saída', 'valor'].sum()
    assert summary['total_inflows'] == pytest.approx(float(expected_in))
    assert summary['total_outflows'] == pytest.approx(float(expected_out))
    assert summary['net_balance'] == pytest.approx(float(expected_in - expected_out))


def test_summary_coverage_inf_when_no_forecast_out():
    from cashflow import metrics as metrics_module

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada', 'Entrada'],
            'status': ['Previsto', 'Pago'],
            'recorrente': ['Não', 'Não'],
            'valor': [100.0, 50.0],
        }
    )
    summary = metrics_module.build_summary(frame)
    assert math.isinf(summary['forecast_coverage'])


def test_summary_coverage_zero_when_no_forecast():
    from cashflow import metrics as metrics_module

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada', 'Saída'],
            'status': ['Pago', 'Pago'],
            'recorrente': ['Não', 'Não'],
            'valor': [100.0, 40.0],
        }
    )
    summary = metrics_module.build_summary(frame)
    assert summary['forecast_coverage'] == 0.0


def test_summary_realized_share_is_volume():
    from cashflow import metrics as metrics_module

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada', 'Saída'],
            'status': ['Recebido', 'Previsto'],
            'recorrente': ['Não', 'Não'],
            'valor': [80.0, 20.0],
        }
    )
    summary = metrics_module.build_summary(frame)
    assert summary['realized_share'] == pytest.approx(0.8)


def test_daily_flow_requires_signed_value():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(KeyError, match='with_signed_value'):
        metrics_module.daily_flow(frame)


def test_daily_flow_values():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    daily = metrics_module.daily_flow(frame)
    assert {'data_prevista', 'net', 'cumulative'} <= set(daily.columns)
    assert daily['net'].sum() == pytest.approx(daily['cumulative'].iloc[-1])
    assert daily['net'].sum() == pytest.approx(frame['signed_value'].sum())


def test_summary_empty_frame_realized_share_zero():
    from cashflow import metrics as metrics_module

    frame = pd.DataFrame(
        {
            'tipo': pd.Series([], dtype='object'),
            'status': pd.Series([], dtype='object'),
            'recorrente': pd.Series([], dtype='object'),
            'valor': pd.Series([], dtype='float'),
        }
    )
    summary = metrics_module.build_summary(frame)
    assert summary['realized_share'] == 0.0
    assert summary['total_inflows'] == 0.0
    assert summary['total_outflows'] == 0.0
    assert summary['net_balance'] == 0.0


def test_summary_net_equals_daily_net_canonical():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    summary = metrics_module.build_summary(frame)
    daily = metrics_module.daily_flow(frame)
    assert summary['net_balance'] == pytest.approx(float(daily['net'].sum()))


def test_summary_net_equals_daily_net_with_nat_injected():
    from cashflow import data as data_module
    from cashflow import metrics as metrics_module

    base = data_module.load_cashflow('data/cash_flow.csv')
    injected = base.copy()
    injected.loc[injected.index[0], 'data_prevista'] = pd.NaT
    signed = data_module.with_signed_value(injected)
    summary = metrics_module.build_summary(signed)
    daily = metrics_module.daily_flow(signed)
    assert summary['net_balance'] == pytest.approx(float(daily['net'].sum()))


def test_build_summary_rejects_nan_valor_direct():
    from cashflow import metrics as metrics_module

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada', 'Saída'],
            'status': ['Pago', 'Pago'],
            'recorrente': ['Não', 'Não'],
            'valor': [100.0, float('nan')],
        }
    )
    with pytest.raises(ValueError, match='n_nulos'):
        metrics_module.build_summary(frame)
