import plotly.graph_objects as go
from dash import dcc, html
from data.queries import fetch_coporate_america_revenue_to_sp500

def layout():
    df = fetch_coporate_america_revenue_to_sp500()

    fig = go.Figure()

    # Total Revenue
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['total_revenue'],
        name="Total Revenue",
        yaxis="y1",
        line=dict(color="#00FF99", width=2.5),
        hovertemplate='Total Revenue: %{y:$.2s}<br>Year: %{x|%Y}<extra></extra>'
    ))

    # S&P 500 Index (average market price)
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['avg_market_price'],
        name="S&P 500 Index",
        yaxis="y2",
        line=dict(color="#3399FF", width=2.5, dash="dot"),
        hovertemplate='S&P 500: %{y:.0f}<br>Year: %{x|%Y}<extra></extra>'
    ))
    # Annotate selected years
    label_years = [2011, 2013, 2015, 2017, 2019, 2021, 2023]
    label_df = df[df['year'].isin(label_years)]

    # Total Revenue Labels
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['total_revenue'],
        mode='markers+text',
        name='Revenue Labels',
        text=[f"${y/1e12:.1f}T" for y in label_df['total_revenue']],
        textposition='top left',
        marker=dict(color='#00FF99', size=6),
        textfont=dict(size=12),
        yaxis='y1',
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
            text="S&P 500 vs Total Revenue of Corporate America",
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

        yaxis=dict(  # Total Revenue
            title="Total Revenue (USD)",
            tickformat="$.2s",
            gridcolor='#333'
        ),

        yaxis2=dict(  # S&P 500 Index
            title="S&P 500 Index Level",
            overlaying='y',
            side='right',
            position=1.0,
            showgrid=False
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
            dcc.Graph(id="sp500-vs-revenue", figure=fig),
        ], className="black-container")
    ])