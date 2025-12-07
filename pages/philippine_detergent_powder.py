from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_detergent_powder
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = philippine_detergent_powder()
    df = df.sort_values(by="date")

    # Column validation
    expected_cols = {"date", "mean_price", "median_price", "sampled_skus"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Main price line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["mean_price"],
        mode="lines",
        name="Average (PHP per 2kg)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per 2kg)",
        line=dict(width=2.5, dash="dash")
    ))

    # ✅ Add sampled SKU count as contextual secondary axis
    fig.add_trace(go.Bar(
        x=df["date"],
        y=df["sampled_skus"],
        name="Sampled SKUs",
        opacity=0.25,
        marker_color=THEME_COLORS["primary"],
        yaxis="y2",
        hovertemplate="SKUs sampled: %{y}<extra></extra>"
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(
            title="Price (PHP per 2kg)"
        ),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True
    )

    return themed_card(
            title="Philippine Detergent Powder Prices (2kg)",
            description="Daily standardized detergent powder pricing and SKU availability across the Philippines.",
            children=[
                dcc.Graph(
                    id="ph-detergent-price",
                    figure=fig,
                    style={"height": "460px"}
                ),
                html.Div([
                    html.Button(
                        "Download CSV",
                        id="download-detergent-btn",
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
                    dcc.Download(id="download-detergent")
                ], style={"textAlign": "right", "marginTop": "12px"})
            ]
        )

@callback(
    Output("download-detergent", "data"),
    Input("download-detergent-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_detergent_data(n_clicks):
    df = philippine_detergent_powder()
    return dcc.send_data_frame(
        df[["date", "mean_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_detergent_powder_2kg.csv",
        index=False
    )

def get_data():
    df = philippine_detergent_powder()
    return df