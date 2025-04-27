from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import fetch_inflation_data
import dash

def layout():
    df = fetch_inflation_data()
    df = df[(df['us_ten_year_interest'] != 0)]

    # Rename columns for better labels in the graph
    df = df.rename(columns={
        'us_ten_year_interest': 'U.S. 10-Year Bond Yield (%)',
        'interpolated_yield_bond': 'German 10-Year Bond Yield (%)'
    })

    fig = px.line(
        df,
        x='date',
        y=['U.S. 10-Year Bond Yield (%)', 'German 10-Year Bond Yield (%)'],
        title='U.S. vs German 10-Year Bond Yields',
        labels={
            'date': 'Date',
            'value': 'Yield (%)',
            'variable': 'Bond'
        }
    )

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(x=0.01, xanchor='left', font=dict(size=22)),
        margin=dict(l=30, r=30, t=60, b=100),
        height=500,
        hovermode='x unified',
        yaxis=dict(gridcolor='#333'),
        hoverlabel=dict(namelength=-1),
        xaxis=dict(
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor='#333'
        ),
        legend=dict(
            title='',
            orientation='h',
            yanchor='bottom',
            y=-0.3,
            xanchor='center',
            x=0.5
        )
    )

    fig.update_traces(line=dict(width=2.5))
    fig.for_each_trace(
        lambda t: t.update(line_color="#00FF99") if t.name == "German 10-Year Bond Yield (%)" else t.update(line_color="#FF5733")
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="bond-yields-comparison", figure=fig),
            html.Div([
                html.Button("Download CSV", id="download-btn-interest-rate-differential-eur-usd", n_clicks=0, style={
                    "backgroundColor": "#FFCC00",
                    "color": "#000",
                    "padding": "10px 20px",
                    "border": "none",
                    "borderRadius": "4px",
                    "fontWeight": "bold",
                    "fontSize": "14px",
                    "cursor": "pointer",
                    "marginTop": "10px",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.3)",
                    "transition": "background-color 0.2s ease-in-out"
                }),
                dcc.Download(id="download-bonds-interest-rate-differential-eur-usd")
            ], style={"textAlign": "center"})
        ], className="black-container")
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