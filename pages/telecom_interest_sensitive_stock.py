from dash import html, dcc, Input, Output, callback
from data.queries import fetch_telecom_interest_sensitive_stock
import plotly.graph_objects as go
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_telecom_interest_sensitive_stock()
    # Calculate y1 (interest rate) min/max
    min_rate = df['interest_rates'].min()
    max_rate = df['interest_rates'].max()
    center_rate = (min_rate + max_rate) / 2
    range_rate = max_rate - min_rate
    buffer_rate = range_rate * 0.1

    # Calculate y2 (cumulative gains) min/max
    min_gain = df['cumulative_gain'].min()
    max_gain = df['cumulative_gain'].max()
    center_gain = (min_gain + max_gain) / 2
    range_gain = max_gain - min_gain
    buffer_gain = range_gain * 0.1

    fig = go.Figure()

    tickers = df['ticker'].unique()
    color_map = {
        'T': '#00FF99',
        'VZ': '#3399FF',
        'CCOI': '#FFCC00',
        'SP500': '#FF66CC'
    }

    # Add cumulative gain lines
    for ticker in tickers:
        fig.add_trace(go.Scatter(
            x=df[df['ticker'] == ticker]['date'],
            y=df[df['ticker'] == ticker]['cumulative_gain'],
            name=f'Cumulative Gain, {ticker}',
            yaxis='y2',
            line=dict(width=2.5, color=color_map.get(ticker, '#AAAAAA')),
            mode='lines'
        ))

    # Add interest rate line (one series only)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['interest_rates'],
        name='Interest Rate',
        yaxis='y1',
        mode='lines+markers',
        line=dict(width=2.5, color='white'),
        fill='tozeroy',
        fillcolor='rgba(255, 255, 255, 0.08)',
        marker=dict(size=4, color='white'),
        hovertemplate='Rate: %{y:.2f}%<br>Date: %{x|%Y-%m-%d}<extra></extra>',
        
    ))

    fig.update_layout(
        title=dict(
            text='Interest Rates and Cumulative Gains by Ticker',
            x=0.01,
            xanchor='left',
            font=dict(size=22)
        ),
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        height=550,
        margin=dict(l=30, r=30, t=60, b=40),
        hovermode='x unified',
        xaxis=dict(
            title='Date',
            tickformat="%b %Y",
            hoverformat="%Y-%m-%d",
            gridcolor='#333'
        ),
        yaxis=dict(
            title='Interest Rate (%)',
            side='left',
            showgrid=True,
            gridcolor='#333',
            zeroline=False,
            range=[center_rate - range_rate/2 - buffer_rate, center_rate + range_rate/2 + buffer_rate]
        ),
        yaxis2=dict(
            title='Cumulative Gain (%)',
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=False,
            range=[center_gain - range_gain/2 - buffer_gain, center_gain + range_gain/2 + buffer_gain]
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,  # Push further down below x-axis labels
            xanchor='center',
            x=0.5,
            font=dict(size=12)
        ),
        hoverlabel=dict(namelength=-1)
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="interest-vs-stock-gain", figure=fig)
        ], className="black-container")
    ])