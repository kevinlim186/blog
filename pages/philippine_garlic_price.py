from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_garlic_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = philippine_garlic_prices()
    df = df.sort_values(by="date")

    fig = go.Figure()

    # Average trace
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["avg_price"],
        mode="lines",
        name="Average (PHP per 375g)",
        line=dict(width=2.5)
    ))

    # Median trace
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per 375g)",
        line=dict(width=2.5, dash="dash")
    ))

    # Sample size trace (THIS WAS ALWAYS MISSING — now fixed)
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

    # Layout theme
    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Price (PHP per 375g)"),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True
    )
    return themed_card(
        title="Philippine Garlic Prices",
        description="Daily standardized garlic prices across the Philippines (375g).",
        children=[
            dcc.Graph(
                id="philippine-garlic-price",
                figure=fig,
                style={"height": "460px"}
            ),

            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-garlic",
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
                dcc.Download(id="download-garlic")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )


@callback(
    Output("download-garlic", "data"),
    Input("download-btn-garlic", "n_clicks"),
    prevent_initial_call=True
)
def download_garlic_data(n_clicks):
    df = philippine_garlic_prices()
    return dcc.send_data_frame(
        df[["date", "avg_price", "median_price", "sampled_skus"]].to_csv,
        "philippine_garlic_price_375g.csv",
        index=False
    )


def get_data():
    return philippine_garlic_prices()

def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "Philippines" },
        ]
    
    res['url'] = 'https://yellowplannet.com/philippine-garlic-bawang-price-trends/'

    return res 