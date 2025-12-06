from dash import html, dcc, Input, Output, callback
from data.queries import fetch_philippine_milk_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card
import plotly.graph_objects as go

def layout():
    df = fetch_philippine_milk_prices()
    df = df[df["category"] != "Cow Milk"]  # Only alternatives
    df = df.sort_values(by="dt")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["dt"], y=df["mean_price"],
        mode="lines",
        name="Average (PHP per Liter)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["dt"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per Liter)",
        line=dict(width=2.5, dash="dash")
    ))

    if "sampled_skus" in df.columns:
        fig.add_trace(go.Bar(
            x=df["dt"], y=df["sampled_skus"],
            name="Sampled SKUs",
            opacity=0.30,
            marker_color=THEME_COLORS["primary"],
            yaxis="y2",
            hovertemplate="SKUs sampled: %{y}<extra></extra>"
        ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Price (PHP per Liter)"),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            y=-0.25,
            x=0.5,
            xanchor="center"
        ),
        autosize=True,
    )

    return html.Div([
        themed_card([
            html.H2("Philippine Non-Dairy Milk Prices — Alternatives", style={
                "color": THEME_COLORS["text"],
                "marginBottom": "6px"
            }),
            html.P(
                "Daily standardized non-dairy milk pricing across the Philippines.",
                style={"color": "#555", "marginTop": 0}
            ),
            dcc.Graph(id="philippine-milk-alt", figure=fig, style={"height": "460px"}),

            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-alt-milk-btn",
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
                dcc.Download(id="download-alt-milk")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ])
    ])

@callback(
    Output("download-alt-milk", "data"),
    Input("download-alt-milk-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_alt_milk_data(n_clicks):
    df = fetch_philippine_milk_prices()
    df = df[df["category"] != "Cow Milk"]

    return dcc.send_data_frame(
        df[["dt", "category", "mean_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_milk_alternative_avg_median.csv",
        index=False
    )

def get_data():
    df = fetch_philippine_milk_prices()
    return df[df["category"] != "Cow Milk"]