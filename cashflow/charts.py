import numpy as np
import plotly.express as px

from cashflow.data import group_daily_net


def base_layout(fig):
    fig.update_layout(
        font_family='system-ui, -apple-system, sans-serif',
        font_color='#1d1d1f',
        font_size=14,
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        autosize=True,
        height=380,
        margin={'l': 72, 'r': 40, 't': 56, 'b': 104},
        legend_title_text='',
        title_font_color='#1d1d1f',
        title_font_size=17,
        legend_font_color='#1d1d1f',
        legend_font_size=12,
        legend_bgcolor='#ffffff',
        legend_bordercolor='#e0e0e0',
        legend_orientation='h',
        legend_yanchor='top',
        legend_y=-0.32,
        legend_xanchor='center',
        legend_x=0.5,
        hoverlabel_bgcolor='#ffffff',
        hoverlabel_font_color='#1d1d1f',
        hoverlabel_bordercolor='#e0e0e0',
    )
    fig.update_xaxes(
        tickfont_color='#7a7a7a',
        tickfont_size=12,
        gridcolor='#f0f0f0',
        linecolor='#e0e0e0',
        zerolinecolor='#e0e0e0',
        title_font_color='#1d1d1f',
        title_font_size=12,
        automargin=True,
        title_standoff=16,
    )
    fig.update_yaxes(
        tickfont_color='#7a7a7a',
        tickfont_size=12,
        gridcolor='#f0f0f0',
        linecolor='#e0e0e0',
        zerolinecolor='#e0e0e0',
        title_font_color='#1d1d1f',
        title_font_size=12,
        automargin=True,
        title_standoff=16,
    )
    return fig


def daily_net_flow(frame):
    grouped = group_daily_net(frame)
    fig = px.bar(
        grouped,
        x='data_prevista',
        y='net',
        title='Fluxo Líquido Diário',
        labels={'data_prevista': 'Data', 'net': 'Líquido'},
        color_discrete_sequence=['#0066cc'],
    )
    fig.update_xaxes(title_text='Data')
    fig.update_yaxes(title_text='Líquido', tickprefix='R$ ')
    return base_layout(fig)


def cumulative_balance(frame):
    grouped = group_daily_net(frame)
    grouped['balance'] = grouped['net'].cumsum()
    fig = px.area(
        grouped,
        x='data_prevista',
        y='balance',
        title='Saldo Acumulado',
        labels={'data_prevista': 'Data', 'balance': 'Saldo'},
        color_discrete_sequence=['#0066cc'],
    )
    fig.update_xaxes(title_text='Data')
    fig.update_yaxes(title_text='Saldo', tickprefix='R$ ')
    return base_layout(fig)


def inflows_by_category(frame):
    inflows = frame[frame['tipo'] == 'Entrada']
    grouped = inflows.groupby('categoria', as_index=False).agg(total=('valor', 'sum'))
    grouped = grouped.sort_values('total')
    fig = px.bar(
        grouped,
        x='total',
        y='categoria',
        orientation='h',
        title='Entradas por Categoria',
        labels={'total': 'Valor', 'categoria': 'Categoria'},
        color_discrete_sequence=['#0066cc'],
    )
    fig.update_xaxes(title_text='Valor', tickprefix='R$ ')
    fig.update_yaxes(title_text='Categoria')
    return base_layout(fig)


def outflows_by_cost_center(frame):
    outflows = frame[frame['tipo'] == 'Saída']
    grouped = outflows.groupby('centro_custo', as_index=False).agg(total=('valor', 'sum'))
    grouped = grouped.sort_values('total')
    fig = px.bar(
        grouped,
        x='total',
        y='centro_custo',
        orientation='h',
        title='Saídas por Centro de Custo',
        labels={'total': 'Valor', 'centro_custo': 'Centro de Custo'},
        color_discrete_sequence=['#0066cc'],
    )
    fig.update_xaxes(title_text='Valor', tickprefix='R$ ')
    fig.update_yaxes(title_text='Centro de Custo')
    return base_layout(fig)


def realized_vs_forecast(frame):
    work = frame.copy()
    status = work['status']
    is_realized = status.isin(['Pago', 'Recebido'])
    is_forecast = status == 'Previsto'
    work['bucket'] = np.select(
        [is_realized, is_forecast],
        ['Realizado', 'Previsto'],
        default='Desconhecido',
    )
    grouped = work.groupby(['bucket', 'tipo'], as_index=False).agg(total=('valor', 'sum'))
    fig = px.bar(
        grouped,
        x='bucket',
        y='total',
        color='tipo',
        barmode='group',
        title='Realizado vs Previsto',
        labels={'bucket': 'Status', 'total': 'Valor', 'tipo': 'Tipo'},
        color_discrete_map={'Entrada': '#0066cc', 'Saída': '#7a7a7a'},
    )
    fig.update_xaxes(title_text='Status')
    fig.update_yaxes(title_text='Valor', tickprefix='R$ ')
    return base_layout(fig)


def recurring_split(frame):
    grouped = frame.groupby(['recorrente', 'tipo'], as_index=False).agg(total=('valor', 'sum'))
    fig = px.bar(
        grouped,
        x='recorrente',
        y='total',
        color='tipo',
        barmode='group',
        title='Recorrente vs Pontual',
        labels={'recorrente': 'Recorrente', 'total': 'Valor', 'tipo': 'Tipo'},
        color_discrete_map={'Entrada': '#0066cc', 'Saída': '#7a7a7a'},
    )
    fig.update_xaxes(title_text='Recorrente')
    fig.update_yaxes(title_text='Valor', tickprefix='R$ ')
    return base_layout(fig)
