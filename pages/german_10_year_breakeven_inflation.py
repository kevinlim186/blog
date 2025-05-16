from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import fetch_inflation_data
import dash


def layout():
    df = fetch_inflation_data()
    df = df.sort_values(by='date') 
    fig = px.line(
        df,
        x='date',
        y='interpolated_german_breakeven_inflation',
        title='German 10-Year Breakeven Inflation',
        labels={
            'date': 'Date',
            'interpolated_german_breakeven_inflation': 'Inflation (%)'
        }
    )

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(x=0.01, xanchor='left', font=dict(size=22)),
        margin=dict(l=30, r=30, t=60, b=40),
        height=500,
        hovermode='x unified',
        yaxis=dict(gridcolor='#333'),
        hoverlabel=dict(
            namelength=-1
        ),
        xaxis=dict(
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor='#333'
        )
    )

    fig.update_traces(line=dict(width=2.5, color='#00FF99'))  # neon green line

    return html.Div([
        html.Div([
            dcc.Graph(id="german-breakeven-inflation-graph", figure=fig),
            html.Div([
                html.Button("Download CSV", id="download-btn", n_clicks=0, style={
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
                dcc.Download(id="download-breakeven-inflation-data")
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])

@callback(
    Output("download-breakeven-inflation-data", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_inflation_data(n_clicks):
    df = fetch_inflation_data()
    return dcc.send_data_frame(df[[ 'date', 'interpolated_german_breakeven_inflation']].to_csv, "german_breakeven_inflation.csv", index=False)