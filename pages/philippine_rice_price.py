from dash import html, dcc, Input, Output, callback
from data.queries import fetch_philippine_rice_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card
import plotly.graph_objects as go

def layout():
    df = fetch_philippine_rice_prices()
    df = df.sort_values(by='date') 
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["avg_price_per_kilo"],
        mode="lines",
        name="Average (PHP per Kilo)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per Kilo)",
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
        yaxis=dict(title="Price (PHP per Kilo)"),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True
    )
    return themed_card(
        title="Philippine Rice Price",
        description="Daily standardized rice pricing across the Philippines.",
        children=[
            dcc.Graph(
                id="philippine-rice-price",
                figure=fig,
                style={"height": "460px"}
            ),
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
                dcc.Download(id="download-rice")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )

@callback(
    Output("download-rice", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_rice_data(n_clicks):
    df = fetch_philippine_rice_prices()
    return dcc.send_data_frame(df[['date', 'avg_price_per_kilo', 'median_price', 'sampled_skus']].to_csv, "philippine_rice_price_avg_median.csv", index=False)


def get_data():
    df = fetch_philippine_rice_prices()
    return df

def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "Philippines" },
        ]
    
    res['url'] = 'https://yellowplannet.com/philippine-rice-price-history/'

    return res 