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
        line=dict(color=THEME_COLORS["primary"], width=2.5),
        hovertemplate='Net Income Change: %{y:.2f}%<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Cumulative change in S&P 500 Index
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['willshire5000_cumulative_change'],
        name="Wilshire 5000 Cumulative Change (%)",
        line=dict(color=THEME_COLORS["secondary"], width=2.5, dash='dot'),
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
        marker=dict(color=THEME_COLORS["primary"], size=6),
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
        marker=dict(color=THEME_COLORS["secondary"], size=6),
        textfont=dict(size=12),
        showlegend=False
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        height=600,
        xaxis=dict(
            title="Year",
            tickformat="%Y",
            gridcolor=THEME_COLORS["grid"],
            showspikes=True,
            spikemode='across',
            spikesnap='cursor'
        ),

        yaxis=dict(
            title="Cumulative Change (%)",
            tickformat=".1f",
            gridcolor=THEME_COLORS["grid"]
        ),

        hoverlabel=dict(namelength=-1)
    )

    return themed_card(
        [
            dcc.Graph(id="wilshire5000-vs-net-income-cumulative", figure=fig)
        ],
        title="Cumulative Change: Wilshire 5000 vs Corporate America Net Income",
        description="A comparison of long-term cumulative performance between U.S. corporate net income and the Wilshire 5000 index."
    )


def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "United States" },
        ]
    
    res['url'] = 'https://yellowplannet.com/wilshire-5000-companies-net-income/'

    return res 