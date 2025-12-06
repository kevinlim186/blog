import plotly.graph_objects as go
from dash import dcc, html
from data.queries import fetch_coporate_america_net_income_to_wilshire
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_coporate_america_net_income_to_wilshire()

    # Normalize to show cumulative % change from the first year
    df = df.sort_values('year')
    df['total_net_income_change'] = (df['total_net_income'] / df['total_net_income'].iloc[0] - 1) * 100
    df['willshire5000_cumulative_change'] = (df['avg_price'] / df['avg_price'].iloc[0] - 1) * 100

    fig = go.Figure()

    # Cumulative change in Total Revenue
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['total_net_income_change'],
        name="Net Income Cumulative Change (%)",
        line=dict(color="#00FF99", width=2.5),
        hovertemplate='Net Income Change: %{y:.2f}%<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Cumulative change in S&P 500 Index
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['willshire5000_cumulative_change'],
        name="Wilshire 5000 Cumulative Change (%)",
        line=dict(color="#3399FF", width=2.5, dash='dot'),
        hovertemplate='Wilshire 5000 Change: %{y:.2f}%<br>Year: %{x|%Y}<extra></extra>'
    ))
    # Label selected years
    label_years = [2011, 2013, 2015, 2017, 2019, 2021, 2023]
    label_df = df[df['year'].isin(label_years)]

    # Labels for Revenue Change
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['total_net_income_change'],
        mode='markers+text',
        name='Net Income Labels',
        text=[f"{y:.0f}%" for y in label_df['total_net_income_change']],
        textposition='top left',
        marker=dict(color='#00FF99', size=6),
        textfont=dict(size=12),
        showlegend=False
    ))

    # Labels for S&P 500 Change
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['willshire5000_cumulative_change'],
        mode='markers+text',
        name='Wilshire 5000 Labels',
        text=[f"{y:.0f}%" for y in label_df['willshire5000_cumulative_change']],
        textposition='top right',
        marker=dict(color='#3399FF', size=6),
        textfont=dict(size=12),
        showlegend=False
    ))

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        height=600,
        margin=dict(l=40, r=60, t=60, b=100),
        title=dict(
            text="Cumulative Change: Wilshire 5000 vs Corporate America Net Income",
            x=0.01,
            xanchor='left',
            font=dict(size=22)
        ),
        hovermode='x unified',

        xaxis=dict(
            title="Year",
            tickformat="%Y",
            gridcolor='#333',
            showspikes=True,
            spikemode='across',
            spikesnap='cursor'
        ),

        yaxis=dict(
            title="Cumulative Change (%)",
            tickformat=".1f",
            gridcolor='#333'
        ),

        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5,
            font=dict(size=12)
        ),

        hoverlabel=dict(namelength=-1)
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="wilshire5000-vs-net-income-cumulative", figure=fig),
        ], className="black-container")
    ])