import pandas as pd
import streamlit as st

from cashflow import charts, data, metrics


def format_brl(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def card_html(label, value, hint):
    return (
        '<div class=\'cash-card\'>'
        f'<div class=\'cash-label\'>{label}</div>'
        f'<div class=\'cash-value\'>{value}</div>'
        f'<div class=\'cash-hint\'>{hint}</div>'
        '</div>'
    )


def apply_style():
    st.markdown(
        '''
        <style>
        :root { color-scheme: light; }
        .stApp { background-color: #f5f5f7; }
        .block-container { max-width: 1440px; padding-top: 32px; padding-bottom: 32px; }
        header[data-testid='stHeader'] { background-color: #f5f5f7; }
        div[data-testid='stDecoration'] { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .cash-hero {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 40px; font-weight: 600; letter-spacing: -0.3px;
            color: #1d1d1f; margin-bottom: 0px;
        }
        .cash-sub {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 17px; font-weight: 400; line-height: 1.47;
            color: #1d1d1f; margin-top: 8px; margin-bottom: 24px;
        }
        div[data-testid='stHorizontalBlock'] {
            gap: 24px; margin-bottom: 32px;
            flex-wrap: nowrap !important;
        }
        div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] {
            min-width: 0 !important;
        }
        div[data-testid='stHorizontalBlock']:has(div[data-testid='stDownloadButton']) {
            gap: 12px !important;
            justify-content: flex-start !important;
            margin-top: 8px !important;
            margin-bottom: 8px !important;
        }
        div[data-testid='stHorizontalBlock']:has(div[data-testid='stDownloadButton']) > div[data-testid='stColumn'] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: auto !important;
        }
        div[data-testid='stVerticalBlock'] {
            gap: 8px !important;
        }
        div[data-testid='stHorizontalBlock']:has(div[data-testid='stSelectbox']) {
            margin-bottom: 0px !important;
        }
        div[data-testid='stHorizontalBlock']:has(div[data-testid='stMultiSelect']) {
            margin-bottom: 0px !important;
        }
        div[data-testid='stHorizontalBlock']:has(.cash-card) {
            margin-bottom: 32px !important;
        }
        div[data-testid='stHorizontalBlock']:has(div[data-testid='stPlotlyChart']) {
            margin-bottom: 16px !important;
        }
        div[data-testid='stSelectbox'] {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }
        div[data-testid='stMultiSelect'] {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }
        .cash-filter-spacer {
            height: 8px;
        }
        div[data-testid='stMarkdownContainer']:has(hr) {
            margin-bottom: 0px !important;
        }
        div[data-testid='stMarkdown'] hr {
            border: none !important;
            border-top: 1px solid #e0e0e0 !important;
            background-color: transparent !important;
            margin: 8px 0px 16px 0px !important;
            opacity: 1 !important;
            height: 1px !important;
        }
        .cash-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            padding: 24px;
            min-width: 0;
        }
        .cash-label {
            font-size: 14px; font-weight: 600; color: #1d1d1f;
            font-family: system-ui, -apple-system, sans-serif;
        }
        .cash-value {
            font-size: 28px; font-weight: 600; color: #1d1d1f;
            font-family: system-ui, -apple-system, sans-serif;
            margin: 8px 0px;
        }
        .cash-hint {
            font-size: 14px; color: #7a7a7a;
            font-family: system-ui, -apple-system, sans-serif;
        }
        div[data-testid='stPlotlyChart'] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            padding: 16px;
            min-width: 0;
            width: 100%;
            max-width: 100%;
            overflow: hidden;
            box-sizing: border-box;
        }
        div[data-testid='stPlotlyChart'] > div {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }
        div[data-testid='stPlotlyChart'] .js-plotly-plot {
            width: 100% !important;
            max-width: 100% !important;
        }
        div[data-testid='stPlotlyChart'] .plot-container {
            width: 100% !important;
            max-width: 100% !important;
        }
        .stSelectbox label p, .stMultiSelect label p {
            color: #1d1d1f !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }
        div[data-testid='stSelectbox'] div.react-aria-ComboBox > div[data-rac] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            color: #1d1d1f !important;
        }
        div[data-testid='stMultiSelect'] div.react-aria-ComboBox > div[data-rac] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            color: #1d1d1f !important;
        }
        div[data-testid='stSelectbox'] div.react-aria-ComboBox > div[data-rac]:focus-within {
            border-color: #0071e3 !important;
            box-shadow: 0 0 0 2px #0071e3 !important;
        }
        div[data-testid='stMultiSelect'] div.react-aria-ComboBox > div[data-rac]:focus-within {
            border-color: #0071e3 !important;
            box-shadow: 0 0 0 2px #0071e3 !important;
        }
        div[data-testid='stSelectbox'] input {
            color: #1d1d1f !important;
            background-color: transparent !important;
        }
        div[data-testid='stMultiSelect'] input {
            color: #1d1d1f !important;
            background-color: transparent !important;
        }
        div[data-testid='stSelectbox'] input::placeholder {
            color: #7a7a7a !important;
        }
        div[data-testid='stMultiSelect'] input::placeholder {
            color: #7a7a7a !important;
        }
        div[data-testid='stMultiSelect'] span[data-tag] {
            background-color: #0066cc !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 9999px !important;
        }
        div[data-testid='stMultiSelect'] span[data-tag] > span {
            color: #ffffff !important;
        }
        div[data-testid='stMultiSelect'] span[data-tag] button {
            color: #ffffff !important;
        }
        div[data-testid='stMultiSelect'] span[data-tag] button svg {
            fill: #ffffff !important;
            stroke: #ffffff !important;
        }
        div[data-testid='stSelectbox'] button svg {
            fill: #7a7a7a !important;
            color: #7a7a7a !important;
        }
        div[data-testid='stMultiSelect'] button[aria-label='Clear all'] svg,
        div[data-testid='stMultiSelect'] button[aria-label='Open'] svg {
            fill: #7a7a7a !important;
            color: #7a7a7a !important;
        }
        div[data-testid='stSelectboxVirtualDropdown'] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
        }
        div[data-testid='stMultiSelectVirtualDropdown'] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
        }
        div[role='listbox'] {
            background-color: #ffffff !important;
            color: #1d1d1f !important;
        }
        div[role='option'] {
            background-color: #ffffff !important;
            color: #1d1d1f !important;
        }
        div[role='option'][data-focused='true'] {
            background-color: #f5f5f7 !important;
            color: #1d1d1f !important;
        }
        div[role='option'][data-selected='true'] {
            color: #1d1d1f !important;
        }
        .stButton > button {
            background-color: #0066cc; color: #ffffff;
            border-radius: 9999px; border: 1px solid #0066cc;
            padding: 11px 22px; font-size: 17px;
            min-width: 110px; height: 44px;
            display: inline-flex; align-items: center; justify-content: center;
            box-sizing: border-box;
        }
        .stButton > button:active { transform: scale(0.95); }
        .stButton > button:focus { outline: 2px solid #0071e3; outline-offset: 2px; }
        .stDownloadButton > button {
            background-color: #ffffff; color: #0066cc;
            border: 1px solid #0066cc; border-radius: 9999px;
            padding: 11px 22px; font-size: 17px;
            min-width: 110px; height: 44px;
            display: inline-flex; align-items: center; justify-content: center;
            box-sizing: border-box;
        }
        .stDownloadButton > button:active { transform: scale(0.95); }
        .stDownloadButton > button:focus { outline: 2px solid #0071e3; outline-offset: 2px; }
        @media (max-width: 640px) {
            .cash-hero { font-size: 34px; }
            .block-container { padding-left: 16px; padding-right: 16px; }
            div[data-testid='stHorizontalBlock'] { gap: 16px; margin-bottom: 24px; flex-wrap: wrap !important; }
            div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] { flex: 1 1 100% !important; }
            div[data-testid='stHorizontalBlock']:has(.cash-card) { margin-bottom: 24px !important; }
            div[data-testid='stHorizontalBlock']:has(div[data-testid='stPlotlyChart']) { margin-bottom: 8px !important; }
        }
        @media (max-width: 419px) {
            .cash-hero { font-size: 28px; }
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def build_filter_options(frame):
    periods = sorted(frame['data_prevista'].dt.strftime('%Y-%m').unique())
    types = sorted(frame['tipo'].unique())
    categories = sorted(frame['categoria'].unique())
    centers = sorted(frame['centro_custo'].unique())
    statuses = sorted(frame['status'].unique())
    recurring_opts = sorted(frame['recorrente'].unique())
    return periods, types, categories, centers, statuses, recurring_opts


def render_filter_fields(periods, types, categories, centers, statuses, recurring_opts):
    top = st.columns(3, gap='medium')
    with top[0]:
        period = st.selectbox('Period', ['All'] + periods, key='period_field')
    with top[1]:
        type_sel = st.multiselect('Type', types, default=types, key='type_field')
    with top[2]:
        category_sel = st.multiselect('Category', categories, default=categories, key='category_field')
    st.markdown('<div class=\'cash-filter-spacer\'></div>', unsafe_allow_html=True)
    bottom = st.columns(3, gap='medium')
    with bottom[0]:
        center_sel = st.multiselect('Cost Center', centers, default=centers, key='center_field')
    with bottom[1]:
        status_sel = st.multiselect('Status', statuses, default=statuses, key='status_field')
    with bottom[2]:
        recurring_sel = st.multiselect('Recurring', recurring_opts, default=recurring_opts, key='recurring_field')
    return period, type_sel, category_sel, center_sel, status_sel, recurring_sel


def render_action_row(filtered):
    row = st.columns([1, 1, 10], gap='small')
    with row[0]:
        reset = st.button('Reset')
    with row[1]:
        st.download_button(
            'Export',
            filtered.to_csv(index=False, sep=';'),
            file_name='cash_flow_filtered.csv',
            mime='text/csv',
        )
    return reset


def render_cards(summary):
    inflow_text = format_brl(summary['total_inflows'])
    outflow_text = format_brl(summary['total_outflows'])
    net_text = format_brl(summary['net_balance'])
    coverage = summary['forecast_coverage']
    coverage_text = f'{coverage:.2f}x'
    cols = st.columns(4, gap='medium')
    with cols[0]:
        st.markdown(card_html('Net Balance', net_text, 'Inflows minus outflows'), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(card_html('Total Inflows', inflow_text, 'All entries'), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(card_html('Total Outflows', outflow_text, 'All exits'), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(card_html('Forecast Coverage', coverage_text, 'Forecast in over forecast out'), unsafe_allow_html=True)


def render_charts(filtered):
    left, right = st.columns(2, gap='medium')
    with left:
        st.plotly_chart(charts.daily_net_flow(filtered), use_container_width=True)
    with right:
        st.plotly_chart(charts.cumulative_balance(filtered), use_container_width=True)
    left, right = st.columns(2, gap='medium')
    with left:
        st.plotly_chart(charts.inflows_by_category(filtered), use_container_width=True)
    with right:
        st.plotly_chart(charts.outflows_by_cost_center(filtered), use_container_width=True)
    left, right = st.columns(2, gap='medium')
    with left:
        st.plotly_chart(charts.realized_vs_forecast(filtered), use_container_width=True)
    with right:
        st.plotly_chart(charts.recurring_split(filtered), use_container_width=True)


def main():
    st.set_page_config(page_title='Cash Flow', layout='wide')
    apply_style()
    st.markdown('<div class=\'cash-hero\'>Cash Flow</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class=\'cash-sub\'>Track liquidity, revenue, costs and forecast risk.</div>',
        unsafe_allow_html=True,
    )
    frame = data.with_signed_value(data.load_cashflow('data/cash_flow.csv'))
    periods, types, categories, centers, statuses, recurring_opts = build_filter_options(frame)
    period, type_sel, category_sel, center_sel, status_sel, recurring_sel = render_filter_fields(
        periods, types, categories, centers, statuses, recurring_opts
    )
    start = None
    end = None
    if period != 'All':
        start = pd.to_datetime(period + '-01')
        end = start + pd.offsets.MonthEnd(0)
    filtered = data.filter_cashflow(
        frame,
        tipos=type_sel,
        categorias=category_sel,
        cost_centers=center_sel,
        statuses=status_sel,
        recurring=recurring_sel,
        start=start,
        end=end,
    )
    reset = render_action_row(filtered)
    if reset:
        for key in ['period_field', 'type_field', 'category_field', 'center_field', 'status_field', 'recurring_field']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    if filtered.empty:
        st.warning('No data for selected filters')
        st.stop()
    st.divider()
    summary = metrics.build_summary(filtered)
    render_cards(summary)
    render_charts(filtered)


if __name__ == '__main__':
    main()
