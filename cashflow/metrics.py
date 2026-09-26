def build_summary(frame):
    inflows = frame.loc[frame['tipo'] == 'Entrada', 'valor'].sum()
    outflows = frame.loc[frame['tipo'] == 'Saída', 'valor'].sum()
    net = float(inflows - outflows)
    forecast_in = frame.loc[
        (frame['tipo'] == 'Entrada') & (frame['status'] == 'Previsto'),
        'valor',
    ].sum()
    forecast_out = frame.loc[
        (frame['tipo'] == 'Saída') & (frame['status'] == 'Previsto'),
        'valor',
    ].sum()
    if forecast_out > 0:
        coverage = float(forecast_in / forecast_out)
    else:
        coverage = 0.0
    realized = frame.loc[
        frame['status'].isin(['Pago', 'Recebido']), 'valor'
    ].sum()
    total = frame['valor'].sum()
    if total > 0:
        realized_share = float(realized / total)
    else:
        realized_share = 0.0
    burn = frame.loc[
        (frame['tipo'] == 'Saída') & (frame['recorrente'] == 'Sim'),
        'valor',
    ].sum()
    return {
        'total_inflows': float(inflows),
        'total_outflows': float(outflows),
        'net_balance': net,
        'forecast_coverage': coverage,
        'realized_share': realized_share,
        'recurring_burn': float(burn),
    }


def daily_flow(frame):
    work = frame.copy()
    grouped = work.groupby('data_prevista', as_index=False).agg(
        net=('signed_value', 'sum')
    )
    grouped = grouped.sort_values('data_prevista')
    grouped['cumulative'] = grouped['net'].cumsum()
    return grouped
