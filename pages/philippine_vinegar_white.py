from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_white_vingar_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = philippine_white_vingar_prices()
    df = df.sort_values(by="date")

    expected_cols = {"date", "mean_price", "median_price", "sampled_skus"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["mean_price"],
        mode="lines",
        name="Average (PHP per 1L)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per 1L)",
        line=dict(width=2.5, dash="dash")
    ))

    fig.add_trace(go.Bar(
        x=df["date"],
        y=df["sampled_skus"],
        name="Sampled SKUs",
        opacity=0.30,
        marker_color=THEME_COLORS["primary"],
        yaxis="y2",
        hovertemplate="SKUs sampled: %{y}<extra></extra>"
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(
            title="Price (PHP per 1L)",
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
        title="Philippine White Vinegar Prices",
         description="Daily white vinegar prices (per 1L) and sampled SKUs across the Philippines.",
        children=[
            dcc.Graph(
                id="whitevinegar-chart",
                figure=fig,
                style={"height": "820px"}, 
            ),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-whitevinegar-btn",
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
                dcc.Download(id="download-whitevinegar")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )


@callback(
    Output("download-whitevinegar", "data"),
    Input("download-whitevinegar-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_whitevinegar_data(n_clicks):
    df = philippine_white_vingar_prices()
    return dcc.send_data_frame(
        df[["date", "mean_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_white_vinegar_1L.csv",
        index=False
    )


def get_data():
    df = philippine_white_vingar_prices()
    return df


def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "Philippines" },
        ]
    
    res['url'] = 'https://yellowplannet.com/philippine-white-vinegar-price-trends'

    return res 