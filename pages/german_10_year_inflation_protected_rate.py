from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import fetch_inflation_data
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_inflation_data()
    df = df.sort_values(by="date")

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["interpolated_yield_tips"],
        mode="lines",
        name="Inflation-Protected Yield (%)",
        line=dict(width=2.5, color=THEME_COLORS["primary"])
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Inflation-Protected Yield (%)"),
        autosize=True,
    )

    return themed_card(
    title="German 10-Year Inflation-Protected Rate",
    description="Daily interpolated real yield for German 10-year inflation-linked bonds.",
    children=[
        dcc.Graph(
            id="german-10-year-inflation-protected-rate",
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
            dcc.Download(id="download-inflation-protected-data")
        ], style={"textAlign": "right", "marginTop": "12px"})
    ]
)

@callback(
    Output("download-inflation-protected-data", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_inflation_data(n_clicks):
    df = fetch_inflation_data()
    return dcc.send_data_frame(df[[ 'date', 'interpolated_yield_tips']].to_csv, "german_inflation_protected_rate.csv", index=False)

def get_data():
    df = fetch_inflation_data()
    df = df[[ 'date', 'interpolated_yield_tips']]
    df = df.sort_values(by='date') 
    return df



def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "Germany" },
        ]
    
    res['url'] = 'https://yellowplannet.com/german-10-year-real-yield-inflation-linked-bund-constant-maturity/'

    return res 