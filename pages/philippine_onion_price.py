from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
import dash
from data.queries import fetch_philippine_onion


def layout():
    df = fetch_philippine_onion()
    df = df.sort_values(by='date')

    fig = px.line(
        df,
        x='date',
        y=['avg_price', 'median_price'],
        title='Philippine Onion Price (Standardized to 375 grams)',
        labels={
            'date': 'Date',
            'avg_price': 'Average Price (PHP, 375g)',
            'median_price': 'Median Price (PHP, 375g)'
        }
    )

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(
            text='Philippine Onion Price (Standardized to 375 grams)',
            x=0.01,
            xanchor='left',
            font=dict(size=26, family='Open Sans', color='white')
        ),
        margin=dict(l=30, r=30, t=100, b=50),
        height=500,
        hovermode='x unified',
        yaxis=dict(gridcolor='#333'),
        hoverlabel=dict(
            namelength=-1
        ),
        xaxis=dict(
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor='#333',
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor="#222222",
                font=dict(color="white", size=13),
                activecolor="#FFCC00"
            ),
            type="date"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=13, family='Open Sans', color='white'),
            bgcolor="rgba(0,0,0,0)"
        )
    )

    # Style: avg = solid, median = dashed
    fig.for_each_trace(
        lambda trace: trace.update(line=dict(width=2.5)) if trace.name == "Average Price (PHP, 375g)"
        else trace.update(line=dict(width=2.5, dash="dash"))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="philippine-onion-price", figure=fig),
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
                dcc.Download(id="download-onion")
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])


@callback(
    Output("download-onion", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_onion_data(n_clicks):
    df = fetch_philippine_onion()
    return dcc.send_data_frame(
        df[['date', 'avg_price', 'median_price']].to_csv,
        "philippine_onion_price_375g.csv",
        index=False
    )