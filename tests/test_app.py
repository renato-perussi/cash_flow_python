import pandas as pd


def test_format_brl_valid():
    from app import format_brl

    assert format_brl(1234.5) == 'R$ 1.234,50'
    assert format_brl(0) == 'R$ 0,00'


def test_format_brl_nan_inf_none():
    import math

    from app import format_brl

    assert format_brl(None) == '—'
    assert format_brl(float('nan')) == '—'
    assert format_brl(float('inf')) == '—'
    assert format_brl(-float('inf')) == '—'
    assert format_brl(pd.NA) == '—'
    assert format_brl(math.inf) == '—'


def test_card_html_escapes():
    from app import card_html

    out = card_html('<b>label</b>', '<i>1</i>', '"hint"&')
    assert '<b>' not in out
    assert '<i>' not in out
    assert '&lt;b&gt;' in out
    assert 'Saldo Líquido' in card_html('Saldo Líquido', 'R$ 1,00', 'hint')


def test_build_filter_options_ignores_nan():
    import numpy as np

    from app import build_filter_options

    frame = pd.DataFrame(
        {
            'tipo': ['Entrada', None],
            'categoria': ['Vendas', np.nan],
            'centro_custo': ['Comercial', 'Adm'],
            'status': ['Pago', 'Pago'],
            'recorrente': ['Sim', 'Não'],
        }
    )
    types, categories, centers, _statuses, _recurring = build_filter_options(frame)
    assert types == ['Entrada']
    assert categories == ['Vendas']
    assert set(centers) == {'Adm', 'Comercial'}


def test_data_path_exists():
    from app import DATA_PATH

    assert str(DATA_PATH).endswith('data/cash_flow.csv')
    assert DATA_PATH.exists()


def test_period_days_full_window():
    from app import PERIOD_DAYS

    assert PERIOD_DAYS['360d'] == 360


def test_get_frame_failure_shows_error(monkeypatch):
    import app as app_module
    from cashflow import data as data_module

    def _boom(_path):
        raise FileNotFoundError('sumiu')

    monkeypatch.setattr(data_module, 'load_cashflow', _boom)
    errors = []
    stopped = []
    monkeypatch.setattr(
        app_module.st, 'error', lambda msg: errors.append(msg)
    )

    def _stop():
        stopped.append(True)
        raise RuntimeError('stopped')

    monkeypatch.setattr(app_module.st, 'stop', _stop)
    try:
        app_module.get_frame.__wrapped__()
    except RuntimeError:
        pass
    assert errors, 'st.error deve ser chamado na falha de load'
    assert stopped, 'st.stop deve ser chamado na falha de load'


def test_get_frame_invalid_data_shows_error(monkeypatch):
    import app as app_module
    from cashflow import data as data_module

    def _boom(_path):
        raise ValueError('csv inválido')

    monkeypatch.setattr(data_module, 'load_cashflow', _boom)
    errors = []
    monkeypatch.setattr(
        app_module.st, 'error', lambda msg: errors.append(msg)
    )

    def _stop():
        raise RuntimeError('stopped')

    monkeypatch.setattr(app_module.st, 'stop', _stop)
    try:
        app_module.get_frame.__wrapped__()
    except RuntimeError:
        pass
    assert errors, 'st.error deve ser chamado em ValueError'


def test_format_brl_bool_returns_dash():
    from app import format_brl

    assert format_brl(True) == '—'
    assert format_brl(False) == '—'


def test_apply_style_includes_alert_contrast(monkeypatch):
    import app as app_module

    captured = []
    monkeypatch.setattr(
        app_module.st, 'markdown', lambda body, **kwargs: captured.append(body)
    )
    app_module.apply_style()
    css = '\n'.join(captured)
    for testid in (
        'stAlertContentWarning',
        'stAlertContentError',
        'stAlertContentInfo',
        'stAlertContentSuccess',
    ):
        assert testid in css, f'regra de contraste ausente para {testid}'
    assert '#1d1d1f' in css, 'texto dos alertas deve usar a tinta ink'


def test_get_frame_keyerror_shows_error(monkeypatch):
    import app as app_module
    from cashflow import data as data_module

    def _boom(_frame):
        raise KeyError("coluna 'tipo' ausente")

    monkeypatch.setattr(data_module, 'with_signed_value', _boom)
    errors = []
    stopped = []
    monkeypatch.setattr(
        app_module.st, 'error', lambda msg: errors.append(msg)
    )

    def _stop():
        stopped.append(True)
        raise RuntimeError('stopped')

    monkeypatch.setattr(app_module.st, 'stop', _stop)
    try:
        app_module.get_frame.__wrapped__()
    except RuntimeError:
        pass
    assert errors, 'st.error deve ser chamado em KeyError'
    assert stopped, 'st.stop deve ser chamado em KeyError'
