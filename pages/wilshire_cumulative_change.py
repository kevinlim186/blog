import plotly.graph_objects as go
from dash import dcc, html
from data.queries import fetch_coporate_america_net_income_to_wilshire

def layout():
    df = fetch_coporate_america_net_income_to_wilshire()

    # Normalize to show cumulative % change from the first year
    df = df.sort_values('year')
    df['total_net_income_change'] = (df['total_net_income'] / df['total_net_income'].iloc[0] - 1) * 100
    df['willshire5000_cumulative_change'] = (df['avg_price'] / df['avg_price'].iloc[0] - 1) * 100

    fig = go.Figure()

    # Cumulative change in Total Net Income
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['total_net_income_change'],
        name="Net Income Cumulative Change (%)",
        line=dict(color="#00FF99", width=2.5),
        hovertemplate='Net Income Change: %{y:.2f}%<br>Year: %{x|%Y}<extra></extra>'
    ))

    # Cumulative change in Wilshire 5000
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

    # Labels for Net Income
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['total_net_income_change'],
        mode='markers+text',
        name='Net Income Labels',
        text=[f"{y:.0f}%" for y in label_df['total_net_income_change']],
        textposition='top center',
        marker=dict(color='#00FF99', size=10),
        textfont=dict(size=22),
        showlegend=False
    ))

    # Labels for Wilshire 5000
    fig.add_trace(go.Scatter(
        x=label_df['year'],
        y=label_df['willshire5000_cumulative_change'],
        mode='markers+text',
        name='Wilshire 5000 Labels',
        text=[f"{y:.0f}%" for y in label_df['willshire5000_cumulative_change']],
        textposition='top center',
        marker=dict(color='#3399FF', size=10),
        textfont=dict(size=22),
        showlegend=False
    ))

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        height=900,  # Pinterest-friendly vertical size
        margin=dict(l=60, r=60, t=100, b=120),
        title=dict(
            text="📊 Corporate America's Net Income vs Wilshire 5000 Growth (2010–2023)",
            x=0.01,
            xanchor='left',
            font=dict(size=20)  # smaller Pinterest-friendly title
        ),
        hovermode='x unified',

        xaxis=dict(
            title="Year",
            tickformat="%Y",
            gridcolor='#333',
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            titlefont=dict(size=20),
            tickfont=dict(size=16)
        ),

        yaxis=dict(
            title="Cumulative Change (%)",
            tickformat=".1f",
            gridcolor='#333',
            titlefont=dict(size=20),
            tickfont=dict(size=16)
        ),

        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5,
            font=dict(size=20)
        ),

        hoverlabel=dict(namelength=-1)
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="wilshire5000-vs-net-income-cumulative", figure=fig),
        ], className="black-container")
    ])