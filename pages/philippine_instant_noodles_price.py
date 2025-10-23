from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import philippine_instant_noodles_price
import dash

def layout():
    df = philippine_instant_noodles_price()
    df = df.sort_values(by='date')
    # Use new column names for noodles
    cols = set(df.columns)
    avg_candidates = ['avg_price', 'avg_noodle_price_per_55g']
    med_candidates = ['median_price', 'median_noodle_price_per_55g']
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
        title='Philippine Instant Noodle Price per 55g (Average vs Median)',
        labels={
            'date': 'Date',
            'avg_price': 'Average (PHP/55g)',
            'median_price': 'Median (PHP/55g)'
        }
    )

    # Rename traces for nicer legend labels
    label_map = {
        avg_col: 'Average (PHP/55g)',
        med_col: 'Median (PHP/55g)'
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
            text='Philippine Instant Noodle Price per 55g (Average vs Median)',
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

    # Style average as solid and median as dashed
    fig.for_each_trace(
        lambda trace: trace.update(line=dict(width=2.5)) if trace.name == "Average (PHP/55g)"
        else trace.update(line=dict(width=2.5, dash="dash"))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="philippine-noodle-price", figure=fig),
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
                dcc.Download(id="download-noodle")
            ], style={"textAlign": "center"}),
            html.P("Note: Prices are standardized at 55 grams per serving.", style={"color": "#cccccc", "fontStyle": "italic", "marginTop": "10px"})
        ], className="black-container")
    ])

@callback(
    Output("download-noodle", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_noodle_data(n_clicks):
    df = fetch_philippine_noodle_prices()
    cols = set(df.columns)
    avg_candidates = ['avg_price', 'avg_noodle_price_per_55g']
    med_candidates = ['median_price', 'median_noodle_price_per_55g']
    avg_col = next((c for c in avg_candidates if c in cols), None)
    med_col = next((c for c in med_candidates if c in cols), None)
    return dcc.send_data_frame(
        df[['date', avg_col, med_col]].to_csv,
        "philippine_noodle_price_per_55g_avg_median.csv",
        index=False
    )