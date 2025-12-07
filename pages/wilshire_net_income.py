import plotly.graph_objects as go
from dash import dcc, html
from data.queries import fetch_coporate_america_net_income_to_wilshire
import numpy as np 
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_coporate_america_net_income_to_wilshire()
    df = df.sort_values('year')
    fig = go.Figure()

    # Total Income
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['total_net_income'],
        name="Total Net Income",
        yaxis="y1",
        line=dict(color=THEME_COLORS["primary"], width=2.5),
        hovertemplate='Total Income: %{y:$.2s}<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Wilshire 5000 Index (average market price)
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['avg_price'],
        name="Wilshire 5000 Index",
        yaxis="y2",
        line=dict(color=THEME_COLORS["secondary"], width=2.5, dash="dot"),
        hovertemplate='Wilshire 5000: %{y:.0f}<br>Year: %{x|%Y}<extra></extra>'
    ))
    # Annotate selected years
    label_years = [2011, 2013, 2015, 2017, 2019, 2021, 2023]
    label_df = df[df['year'].isin(label_years)]

    # Total Income Labels
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['total_net_income'],
        mode='markers+text',
        name='Income Labels',
        text = [f"${y/1e9:.1f}B" for y in label_df['total_net_income']],
        textposition='top left',
        marker=dict(color=THEME_COLORS["primary"], size=6),
        textfont=dict(size=12),
        yaxis='y1',
        showlegend=False
    ))

    income_min = df['total_net_income'].min()
    income_max = df['total_net_income'].max()
    index_min = df['avg_price'].min()
    index_max = df['avg_price'].max()

    income_buffer = (income_max - income_min) * 0.1
    index_buffer = (index_max - index_min) * 0.1

    ticks = np.linspace(income_min, income_max, 5)
    tickvals = ticks
    ticktext = [f"${x/1e9:.1f}B" for x in ticks]

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
            title="Net Income (USD)",
            tickvals=tickvals.tolist(),
            ticktext=ticktext,
            gridcolor=THEME_COLORS["grid"]
        ),

        yaxis2=dict(
            title="Wilshire 5000 Index Level",
            overlaying='y',
            side='right',
            position=1.0,
            showgrid=False,
            range=[index_min - index_buffer, index_max + index_buffer]
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
    return themed_card(
        title="Wilshire 5000 vs Total Net Income of Corporate America",
        description="A long-term comparison of corporate America's net income against movements in the Wilshire 5000 index.",
        children=[
            dcc.Graph(id="wilshire-vs-net-income", figure=fig)
        ]
    )