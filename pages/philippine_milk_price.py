from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import fetch_philippine_milk_prices
import dash

def layout():
    df = fetch_philippine_milk_prices()
    df = df.sort_values(by='dt').reset_index(drop=True)

    fig_avg = px.line(
        df,
        x='dt',
        y='avg_price_per_liter',
        color='category',
        title='Philippine Milk Price per Liter (Average) by Category',
        labels={
            'dt': 'Date',
            'avg_price_per_liter': 'Average (PHP/Liter)',
            'category': 'Category'
        }
    )

    fig_avg.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(
            text='Philippine Milk Price per Liter (Average) by Category',
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
            # rangeslider=dict(visible=True),
            type="date"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,
            xanchor="right",
            x=1.0,
            font=dict(size=13, family='Open Sans', color='white')
        )
    )

    fig_avg.for_each_trace(
        lambda trace: trace.update(line=dict(width=2.5))
    )

    fig_median = px.line(
        df,
        x='dt',
        y='median_price_per_liter',
        color='category',
        title='Philippine Milk Price per Liter (Median) by Category',
        labels={
            'dt': 'Date',
            'median_price_per_liter': 'Median (PHP/Liter)',
            'category': 'Category'
        }
    )

    fig_median.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(
            text='Philippine Milk Price per Liter (Median) by Category',
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
            # rangeslider=dict(visible=True),
            type="date"
        ),
        legend=dict(
            orientation="h",       # horizontal layout
            yanchor="bottom",      # anchor the legend box at its bottom
            y=-0.3,                # move it below the chart (negative pushes outside)
            xanchor="center",
            x=0.5,                 # center horizontally
            font=dict(size=13, family='Open Sans', color='white'),
            bgcolor="rgba(0,0,0,0)",  # optional: transparent background
        )
    )

    fig_median.for_each_trace(
        lambda trace: trace.update(line=dict(width=2.5))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="philippine-milk-price-avg", figure=fig_avg),
            dcc.Graph(id="philippine-milk-price-median", figure=fig_median),
            html.Div([
                html.Button("Download Milk CSV", id="download-btn", n_clicks=0, style={
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
                dcc.Download(id="download-milk")
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])

@callback(
    Output("download-milk", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_milk_data(n_clicks):
    df = fetch_philippine_milk_prices()
    return dcc.send_data_frame(
        df[['dt', 'category', 'avg_price_per_liter', 'median_price_per_liter']].to_csv,
        "philippine_milk_price_per_liter_avg_median.csv",
        index=False
    )