import pandas as pd
import pytest


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


def test_charts_have_data():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    for fig in [
        charts_module.daily_net_flow(frame),
        charts_module.cumulative_balance(frame),
        charts_module.inflows_by_category(frame),
        charts_module.outflows_by_cost_center(frame),
        charts_module.realized_vs_forecast(frame),
        charts_module.recurring_split(frame),
    ]:
        assert len(fig.data) > 0


def test_daily_net_flow_values():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    fig = charts_module.daily_net_flow(frame)
    expected = frame.groupby('data_prevista')['signed_value'].sum().sort_index()
    assert len(fig.data[0].x) == len(expected)
    assert float(sum(fig.data[0].y)) == pytest.approx(float(expected.sum()))


def test_cumulative_balance_values():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    fig = charts_module.cumulative_balance(frame)
    assert len(fig.data) > 0
    assert float(fig.data[0].y[-1]) == pytest.approx(
        float(frame['signed_value'].sum())
    )


def test_daily_charts_require_signed_value():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.load_cashflow('data/cash_flow.csv')
    with pytest.raises(KeyError, match='with_signed_value'):
        charts_module.daily_net_flow(frame)
    with pytest.raises(KeyError, match='with_signed_value'):
        charts_module.cumulative_balance(frame)


def test_realized_vs_forecast_unknown_bucket():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    ).copy()
    extra = frame.iloc[:1].copy()
    extra['status'] = 'Invalido'
    mixed = pd.concat([frame, extra], ignore_index=True)
    fig = charts_module.realized_vs_forecast(mixed)
    assert len(fig.data) > 0
    labels = set()
    for trace in fig.data:
        labels.update(list(trace.x))
    assert 'Desconhecido' in labels
    assert {'Realizado', 'Previsto'} <= labels


def test_realized_vs_forecast_valid_buckets_unchanged():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    )
    fig = charts_module.realized_vs_forecast(frame)
    labels = set()
    for trace in fig.data:
        labels.update(list(trace.x))
    assert labels <= {'Realizado', 'Previsto'}


def test_valor_charts_reject_negative_valor():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    base = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    ).head(5).copy()
    base.loc[base.index[0], 'valor'] = -999.0
    with pytest.raises(ValueError, match='não-positivos'):
        charts_module.inflows_by_category(base)
    with pytest.raises(ValueError, match='não-positivos'):
        charts_module.outflows_by_cost_center(base)
    with pytest.raises(ValueError, match='não-positivos'):
        charts_module.realized_vs_forecast(base)
    with pytest.raises(ValueError, match='não-positivos'):
        charts_module.recurring_split(base)


def test_valor_charts_reject_inf_valor():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    base = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    ).head(5).copy()
    base.loc[base.index[0], 'valor'] = float('inf')
    with pytest.raises(ValueError, match='inf'):
        charts_module.inflows_by_category(base)
    with pytest.raises(ValueError, match='inf'):
        charts_module.outflows_by_cost_center(base)
    with pytest.raises(ValueError, match='inf'):
        charts_module.realized_vs_forecast(base)
    with pytest.raises(ValueError, match='inf'):
        charts_module.recurring_split(base)


def test_valor_charts_empty_frame_ok():
    import pandas as pd

    from cashflow import charts as charts_module
    from cashflow import data as data_module

    frame = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    ).head(0).copy()
    assert charts_module.inflows_by_category(frame) is not None
    assert charts_module.outflows_by_cost_center(frame) is not None
    assert charts_module.realized_vs_forecast(frame) is not None
    assert charts_module.recurring_split(frame) is not None
    assert pd.isna(frame['valor']).sum() == 0


def test_valor_charts_missing_valor_raises_friendly():
    from cashflow import charts as charts_module
    from cashflow import data as data_module

    base = data_module.with_signed_value(
        data_module.load_cashflow('data/cash_flow.csv')
    ).head(5).copy()
    no_valor = base.drop(columns=['valor'])
    assert 'valor' not in no_valor.columns
    with pytest.raises(ValueError, match='colunas ausentes'):
        charts_module.inflows_by_category(no_valor)
    with pytest.raises(ValueError, match='colunas ausentes'):
        charts_module.outflows_by_cost_center(no_valor)
    with pytest.raises(ValueError, match='colunas ausentes'):
        charts_module.realized_vs_forecast(no_valor)
    with pytest.raises(ValueError, match='colunas ausentes'):
        charts_module.recurring_split(no_valor)
