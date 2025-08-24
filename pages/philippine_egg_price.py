from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import fetch_philippine_egg_prices
import dash

def layout():
    df = fetch_philippine_egg_prices()
    df = df.sort_values(by='date')
    # Be flexible with column names (old vs new aliases)
    cols = set(df.columns)
    avg_candidates = ['avg_egg_price_per_pc', 'avg_price_per_pc']
    med_candidates = ['median_egg_price_per_pc', 'median_pc']
    avg_col = next((c for c in avg_candidates if c in cols), None)
    med_col = next((c for c in med_candidates if c in cols), None)
    if not avg_col or not med_col:
        raise ValueError(
            f"Expected one of {avg_candidates} and {med_candidates} in DataFrame columns, got: {sorted(df.columns)}"
        )
    fig = px.line(
        df,
        x='date',
        y=[avg_col, med_col],
        title='Philippine Medium Egg Price per Piece (Average vs Median)',
        labels={
            'date': 'Date',
            'avg_egg_price_per_pc': 'Average (PHP/pc)',
            'median_egg_price_per_pc': 'Median (PHP/pc)'
        }
    )

    # Rename traces for nicer legend labels
    label_map = {
        avg_col: 'Average (PHP/pc)',
        med_col: 'Median (PHP/pc)'
    }
    for tr in fig.data:
        if tr.name in label_map:
            tr.name = label_map[tr.name]

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(
            text='Philippine Egg Price per Piece (Average vs Median)',
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

    # Style average as solid and median as dashed
    fig.for_each_trace(
        lambda trace: trace.update(line=dict(width=2.5)) if trace.name == "Average (PHP/pc)"
        else trace.update(line=dict(width=2.5, dash="dash"))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="philippine-egg-price", figure=fig),
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
                dcc.Download(id="download-egg")
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])

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
        df[['date', avg_col, med_col]].to_csv,
        "philippine_egg_price_per_piece_avg_median.csv",
        index=False
    )