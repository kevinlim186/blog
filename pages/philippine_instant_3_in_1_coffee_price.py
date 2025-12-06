from dash import html, dcc, Input, Output, callback
from data.queries import philippine_instant_3_in_1_coffee_price
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card
import plotly.graph_objects as go

def layout():
    df = philippine_instant_3_in_1_coffee_price()
    df = df.sort_values(by='date')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'], y=df['mean_price'],
        mode='lines',
        name='Average (PHP per 400g)',
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df['date'], y=df['median_price'],
        mode='lines',
        name='Median (PHP per 400g)',
        line=dict(width=2.5, dash='dash')
    ))

    if 'sampled_skus' in df.columns:
        fig.add_trace(go.Bar(
            x=df['date'], y=df['sampled_skus'],
            name='Sampled SKUs',
            opacity=0.30,
            marker_color=THEME_COLORS['primary'],
            yaxis='y2',
            hovertemplate='SKUs sampled: %{y}<extra></extra>'
        ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title='Price (PHP per 400g)'),
        yaxis2=dict(
            title='Sample Size (SKUs)',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation='h',
            y=-0.25,
            x=0.5,
            xanchor='center'
        ),
        autosize=True
    )

    return html.Div([
        themed_card([
            html.H2("Philippine Instant 3-in-1 Coffee Price", style={
                "color": THEME_COLORS["text"],
                "marginBottom": "6px"
            }),
            html.P(
                "Daily standardized instant 3-in-1 coffee pricing across the Philippines.",
                style={"color": "#555", "marginTop": 0}
            ),
            dcc.Graph(id="philippine-coffee-price", figure=fig, style={"height": "460px"}),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn",
                    n_clicks=0,
                    style={
                        "backgroundColor": THEME_COLORS["primary"],
                        "color": "#FFF",
                        "padding": "10px 22px",
                        "border": "none",
                        "borderRadius": "6px",
                        "fontWeight": "600",
                        "cursor": "pointer",
                        "fontSize": "14px",
                        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
                    }
                ),
                dcc.Download(id="download-coffee")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ])
    ])

@callback(
    Output("download-coffee", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_coffee_data(n_clicks):
    df = philippine_instant_3_in_1_coffee_price()
    return dcc.send_data_frame(
        df[['date', 'mean_price', 'median_price', 'sampled_skus']].to_csv,
        "philippine_instant_coffee_price_per_400g_avg_median.csv",
        index=False
    )

def get_data():
    df = philippine_instant_3_in_1_coffee_price()
    return df