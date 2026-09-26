import pandas as pd


def load_cashflow(path):
    frame = pd.read_csv(path, sep=';')
    frame['data_prevista'] = pd.to_datetime(frame['data_prevista'])
    frame['data_realizada'] = pd.to_datetime(
        frame['data_realizada'], errors='coerce'
    )
    frame['valor'] = frame['valor'].astype(float)
    return frame


def with_signed_value(frame):
    result = frame.copy()
    result['signed_value'] = result.apply(
        lambda row: row['valor']
        if row['tipo'] == 'Entrada'
        else -row['valor'],
        axis=1,
    )
    return result


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
    result = frame.copy()
    if tipos:
        result = result[result['tipo'].isin(tipos)]
    if categorias:
        result = result[result['categoria'].isin(categorias)]
    if cost_centers:
        result = result[result['centro_custo'].isin(cost_centers)]
    if statuses:
        result = result[result['status'].isin(statuses)]
    if recurring:
        result = result[result['recorrente'].isin(recurring)]
    if start is not None:
        result = result[result['data_prevista'] >= pd.to_datetime(start)]
    if end is not None:
        result = result[result['data_prevista'] <= pd.to_datetime(end)]
    return result
