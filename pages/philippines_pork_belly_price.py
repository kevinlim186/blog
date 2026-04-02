import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_pork_belly_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = philippine_pork_belly_prices()
    df = df.sort_values(by="date")

    fig = go.Figure()

    # Average trace
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["avg_price"],
        mode="lines",
        name="Average (PHP per kg)",
        line=dict(width=2.5, color=THEME_COLORS["primary"])
    ))

    # Median trace
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per kg)",
        line=dict(width=2.5, dash="dash", color=THEME_COLORS["secondary"])
    ))

    # Sample size trace
    if "sampled_skus" in df.columns:
        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["sampled_skus"],
            name="Sampled SKUs",
            opacity=0.25,
            marker_color="#A9A9A9",
            yaxis="y2",
            hovertemplate="SKUs sampled: %{y}<extra></extra>"
        ))

    # Layout theme
    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Price (PHP per kg)"),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True
    )

    return themed_card(
        title="Philippine Pork Belly (Liempo) Prices",
        description="Daily standardized retail prices for pork belly across major Philippine markets (normalized to 1kg).",
        children=[
            dcc.Graph(
                id="philippine-pork-price",
                figure=fig,
                style={"height": "460px"}
            ),

            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-pork",
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
                dcc.Download(id="download-pork")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )


@callback(
    Output("download-pork", "data"),
    Input("download-btn-pork", "n_clicks"),
    prevent_initial_call=True
)
def download_pork_data(n_clicks):
    df = philippine_pork_belly_prices()
    return dcc.send_data_frame(
        df[["date", "avg_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_pork_belly_price_1kg.csv",
        index=False
    )


def get_data():
    return philippine_pork_belly_prices()

def get_meta_data():
    return {
        'spatial_coverage': [{"@type": "Place", "name": "Philippines"}],
        'url': 'https://yellowplannet.com/philippine-pork-belly-liempo-price-trends/'
    }