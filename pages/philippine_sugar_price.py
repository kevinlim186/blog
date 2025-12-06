from dash import html, dcc, Input, Output, ctx, callback
import plotly.graph_objects as go
from data.queries import fetch_philippine_sugar_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_philippine_sugar_prices()
    df = df.sort_values(by="date")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["avg_price_per_kilo"],
        mode="lines",
        name="Average (PHP/kg)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP/kg)",
        line=dict(width=2.5, dash="dash")
    ))

    if "sampled_skus" in df.columns:
        fig.add_trace(go.Bar(
            x=df["date"], y=df["sampled_skus"],
            name="Sampled SKUs",
            opacity=0.30,
            marker_color=THEME_COLORS["primary"],
            yaxis="y2",
            hovertemplate="SKUs sampled: %{y}<extra></extra>"
        ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Price (PHP/kg)"),
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
        autosize=True
    )

    return html.Div([
        themed_card([
            html.H2("Philippine Refined Sugar Price", style={
                "color": THEME_COLORS["text"],
                "marginBottom": "6px"
            }),
            html.P(
                "Daily standardized refined sugar pricing across the Philippines.",
                style={"color": "#555", "marginTop": 0}
            ),
            dcc.Graph(id="philippine-sugar-price", figure=fig, style={"height": "460px"}),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-sugar-btn",
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
                dcc.Download(id="download-sugar")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ])
    ])

@callback(
    Output("download-sugar", "data"),
    Input("download-sugar-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_sugar_data(n_clicks):
    df = fetch_philippine_sugar_prices()
    return dcc.send_data_frame(
        df[["date", "avg_price_per_kilo", "median_price", "sampled_skus"]].to_csv,
        "philippine_sugar_price_avg_median.csv",
        index=False
    )

def get_data():
    df = fetch_philippine_sugar_prices()
    return df