from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.queries import fetch_inflation_data
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_inflation_data()
    df = df[(df['us_ten_year_interest'] != 0)]

    # Rename columns for better labels in the graph
    df = df.rename(columns={
        'us_ten_year_interest': 'U.S. 10-Year Bond Yield (%)',
        'interpolated_yield_bond': 'German 10-Year Bond Yield (%)'
    })

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["U.S. 10-Year Bond Yield (%)"],
        mode="lines",
        name="U.S. 10-Year Bond Yield (%)",
        line=dict(width=2.5, color=THEME_COLORS["primary"])
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["German 10-Year Bond Yield (%)"],
        mode="lines",
        name="German 10-Year Bond Yield (%)",
        line=dict(width=2.5, dash="dash", color="#888")
    ))

    fig.update_layout(
        **CHART_TEMPLATE,
        yaxis=dict(title="Yield (%)"),
        autosize=True,
        legend=dict(
            orientation="h",
            y=-0.25,
            x=0.5,
            xanchor="center"
        )
    )

    return html.Div([
        themed_card([
            html.H2("U.S. vs German 10-Year Bond Yields", style={
                "color": THEME_COLORS["text"],
                "marginBottom": "6px"
            }),
            html.P(
                "Comparison of long-term interest rates between U.S. and Germany.",
                style={"color": "#555", "marginTop": 0}
            ),
            dcc.Graph(id="bond-yields-comparison", figure=fig, style={"height": "460px"}),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-interest-rate-differential-eur-usd",
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
                dcc.Download(id="download-bonds-interest-rate-differential-eur-usd")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ])
    ])

@callback(
    Output("download-bonds-interest-rate-differential-eur-usd", "data"),
    Input("download-btn-interest-rate-differential-eur-usd", "n_clicks"),
    prevent_initial_call=True
)
def download_inflation_data(n_clicks):
    df = fetch_inflation_data()
    df = df[(df['us_ten_year_interest'] != 0)]
    return dcc.send_data_frame(
        df[['date', 'us_ten_year_interest', 'interpolated_yield_bond']]
        .rename(columns={
            'us_ten_year_interest': 'U.S. 10-Year Bond Yield (%)',
            'interpolated_yield_bond': 'German 10-Year Bond Yield (%)'
        })
        .to_csv,
        "us_german_10_year_bonds.csv",
        index=False
    )

def get_data():
    df = fetch_inflation_data()
    df = df[(df['us_ten_year_interest'] != 0)]
    df = df[['date', 'us_ten_year_interest', 'interpolated_yield_bond']]
    df = df.sort_values(by='date') 
    return df