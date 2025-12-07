from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_instant_noodles_price
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card


def layout():
    df = philippine_instant_noodles_price()
    df = df.sort_values(by="date")

    # Fixed column names – no more candidates
    avg_col = "mean_price"
    med_col = "median_price"

    # Create figure under unified theme
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df[avg_col],
        mode="lines",
        name="Average (PHP per 55g)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df[med_col],
        mode="lines",
        name="Median (PHP per 55g)",
        line=dict(width=2.5, dash="dash")
    ))

    # Add sampled SKUs if present
    if "sampled_skus" in df.columns:
        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["sampled_skus"],
            name="Sampled SKUs",
            opacity=0.30,
            marker_color=THEME_COLORS["primary"],
            yaxis="y2",
            hovertemplate="SKUs sampled: %{y}<extra></extra>"
        ))

    # Apply theme layout
    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(
            title="Price (PHP per 55g)"
        ),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True,
    )
    return themed_card(
        title="Philippine Instant Noodle Prices",
        description="Daily standardized instant noodle pricing and SKU availability across the Philippines.",
        children=[
            dcc.Graph(
                id="philippine-noodle-price",
                figure=fig,
                style={"height": "460px"}
            ),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-noodle-btn",
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
                dcc.Download(id="download-noodle")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )

@callback(
    Output("download-noodle", "data"),
    Input("download-noodle-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_noodle_data(n_clicks):
    df = philippine_instant_noodles_price()
    return dcc.send_data_frame(
        df[["date", "mean_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_noodle_price_55g.csv",
        index=False
    )

def get_data():
    df = philippine_instant_noodles_price()
    return df