import pandas as pd
import plotly.graph_objects as go


def plot_equity_curve_matplotlib(curve_df: pd.DataFrame, drawdown: pd.Series, save_path: str | None = None):
    import matplotlib.pyplot as plt
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(curve_df.index, curve_df['equity'], label='Equity', lw=2)
    ax1.set_title('Equity Curve')
    ax1.set_ylabel('Equity')
    ax1.grid(True)
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)


def create_html_dashboard(curve_df: pd.DataFrame, drawdown: pd.Series, trades_df: pd.DataFrame, metrics: dict,
                          save_path: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve_df.index, y=curve_df['equity'], mode='lines', name='Equity Curve'))
    fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown.values, fill='tozeroy', mode='lines', name='Drawdown',
                             opacity=0.2))
    if trades_df is not None and len(trades_df) > 0:
        fig.add_trace(go.Scatter(x=trades_df['entry_time'], y=trades_df['entry'], mode='markers', name='BUY',
                                 marker=dict(symbol='triangle-up', size=10)))
        fig.add_trace(go.Scatter(x=trades_df['exit_time'], y=trades_df['exit'], mode='markers', name='SELL',
                                 marker=dict(symbol='triangle-down', size=10)))
    fig.update_layout(title='Equity Dashboard', xaxis_title='Time', yaxis_title='Value',
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    kpis = {
        "Total Return (%)": f"{metrics.get('total_return', 0):.2f}",
        "Sharpe": f"{metrics.get('sharpe_ratio', 0):.2f}",
        "Max Drawdown (%)": f"{metrics.get('max_drawdown', 0):.2f}",
        "Win Rate (%)": f"{metrics.get('win_rate', 0):.2f}",
        "Profit Factor": f"{metrics.get('profit_factor', 0):.2f}",
        "# Trades": str(metrics.get('num_trades', 0)),
        "Start Equity": f"{metrics.get('start_equity', 0):,.2f}",
        "End Equity": f"{metrics.get('end_equity', 0):,.2f}",
    }
    kpi_text = "<br>".join([f"<b>{k}:</b> {v}" for k, v in kpis.items()])
    fig.add_annotation(xref="paper", yref="paper", x=1.0, y=0.0, xanchor="right", yanchor="bottom",
                       text=kpi_text, showarrow=False, align="right",
                       bordercolor="black", borderwidth=1, bgcolor="white", opacity=0.9)
    fig.write_html(save_path, include_plotlyjs="cdn")
