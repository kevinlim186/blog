from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import philippine_cooking_oil
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = philippine_cooking_oil()
    df = df.sort_values(by='date')

    avg_col = 'mean_price'
    med_col = 'median_price'

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[avg_col],
        mode="lines",
        name="Average (PHP/L)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[med_col],
        mode="lines",
        name="Median (PHP/L)",
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
            title="Price (PHP/L)"
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
            title="Philippine Cooking Oil Prices",
            description="Daily standardized cooking oil pricing across the Philippines.",
            children=[
                dcc.Graph(
                    id="philippine-cooking-oil-price",
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
                    dcc.Download(id="download-cooking-oil")
                ], style={"textAlign": "right", "marginTop": "12px"}),

                html.P(
                    "Note: Prices are standardized to PHP per liter.",
                    style={"color": THEME_COLORS["textMuted"], "fontStyle": "italic", "marginTop": "10px"}
                )
            ]
        )

@callback(
    Output("download-cooking-oil", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_oil_data(n_clicks):
    df = philippine_cooking_oil()
    return dcc.send_data_frame(
        df[['date', 'mean_price', 'median_price', 'sampled_skus']].to_csv,
        "philippine_cooking_oil_price.csv",
        index=False
    )

def get_data():
    df = philippine_cooking_oil()
    return df