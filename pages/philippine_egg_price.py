from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import fetch_philippine_egg_prices
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_philippine_egg_prices()
    df = df.sort_values(by='date')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df['avg_price_per_pc'],
        mode="lines",
        name="Average (PHP/pc)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df['median_pc'],
        mode="lines",
        name="Median (PHP/pc)",
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
        yaxis=dict(title="Price (PHP per piece)"),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        autosize=True
    )

    return themed_card(
        title="Philippine Egg Prices (Per Piece)",
        description="Daily standardized average and median egg prices across the Philippines.",
        children=[
            dcc.Graph(
                id="philippine-egg-price",
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
                dcc.Download(id="download-egg")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )

@callback(
    Output("download-egg", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_egg_data(n_clicks):
    df = fetch_philippine_egg_prices()
    cols = set(df.columns)
    avg_candidates = ['avg_egg_price_per_pc', 'avg_price_per_pc']
    med_candidates = ['median_egg_price_per_pc', 'median_pc']
    avg_col = next((c for c in avg_candidates if c in cols), None)
    med_col = next((c for c in med_candidates if c in cols), None)
    return dcc.send_data_frame(
        df[['date', avg_col, med_col, 'sampled_skus']].to_csv,
        "philippine_egg_price_per_piece_avg_median.csv",
        index=False
    )


def get_data():
    df = fetch_philippine_egg_prices()
    return df