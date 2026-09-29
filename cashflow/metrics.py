"""Métricas agregadas do cash-flow."""

import logging

from cashflow.data import group_daily_net

logger = logging.getLogger(__name__)


def build_summary(frame):
    """Resumo de entradas, saídas, cobertura prevista e burn recorrente.

    forecast_coverage é forecast_in / forecast_out; retorna float('inf')
    quando há forecast_in > 0 sem forecast_out, e 0.0 quando ambos são 0.
    realized_share é participação em volume: realizado (Pago/Recebido)
    sobre total (in + out em volume, ambos positivos em 'valor').

    Alinhamento com group_daily_net/daily_flow: linhas com
    data_prevista NaT são excluídas (com warning) antes de somar,
    pois o groupby diário ignora NaT — sem isso, summary.net
    divergiria da soma diária (ex.: 1 NaT injetado gerava
    diff de -2049.30 no dataset canônico). Sem NaT o resultado é
    idêntico ao contrato anterior. Frames sem coluna
    data_prevista (ex.: fixtures mínimas) somam todas as linhas.

    Pré-condição: chame with_signed_value antes; NaN em 'valor'
    levanta ValueError (defesa direta além do pipeline).
    """
    if 'valor' in frame.columns and frame['valor'].isna().any():
        n_nan = int(frame['valor'].isna().sum())
        raise ValueError(
            f"valores ausentes (NaN) em coluna 'valor': n_nulos={n_nan} "
            '(chame with_signed_value antes)'
        )
    if 'data_prevista' in frame.columns:
        n_nat = int(frame['data_prevista'].isna().sum())
        if n_nat:
            logger.warning(
                'build_summary: excluindo %d linha(s) com data_prevista NaT',
                n_nat,
            )
            frame = frame.dropna(subset=['data_prevista'])
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
    elif forecast_in > 0:
        coverage = float('inf')
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
    """Fluxo líquido diário + acumulado (requer signed_value)."""
    grouped = group_daily_net(frame)
    grouped['cumulative'] = grouped['net'].cumsum()
    return grouped
