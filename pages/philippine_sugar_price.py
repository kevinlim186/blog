from dash import html, dcc, Input, Output, ctx, callback
import plotly.express as px
from data.queries import fetch_philippine_sugar_prices
import dash

def layout():
    df = fetch_philippine_sugar_prices()
    df = df.sort_values(by="date")

    # Flexible column name matching
    cols = set(df.columns)
    avg_candidates = ["avg_price_per_kilo", "avg_kg_price"]
    med_candidates = ["median_price", "median_kg_price"]

    avg_col = next((c for c in avg_candidates if c in cols), None)
    med_col = next((c for c in med_candidates if c in cols), None)

    if not avg_col or not med_col:
        raise ValueError(
            f"Expected one of {avg_candidates} or {med_candidates} in DataFrame columns, got: {sorted(df.columns)}"
        )

    fig = px.line(
        df,
        x="date",
        y=[avg_col, med_col],
        title="Philippine Refined Sugar Price per Kilo (Average vs Median)",
        labels={
            "date": "Date",
            avg_col: "Average (PHP/kg)",
            med_col: "Median (PHP/kg)",
        }
    )

    # Rename trace names for clean legend labels
    label_map = {
        avg_col: "Average (PHP/kg)",
        med_col: "Median (PHP/kg)"
    }
    for tr in fig.data:
        if tr.name in label_map:
            tr.name = label_map[tr.name]

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font=dict(color="white", family="Arial"),
        title=dict(
            text="Philippine Sugar Price per Kilo (Average vs Median)",
            x=0.01,
            xanchor="left",
            font=dict(size=26, family="Open Sans", color="white"),
        ),
        margin=dict(l=30, r=30, t=100, b=50),
        height=500,
        hovermode="x unified",
        yaxis=dict(gridcolor="#333"),
        hoverlabel=dict(namelength=-1),
        xaxis=dict(
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
            gridcolor="#333",
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
            font=dict(size=13, family="Open Sans", color="white"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    # Line styling
    fig.for_each_trace(
        lambda tr: tr.update(line=dict(width=2.5))
        if tr.name == "Average (PHP/kg)"
        else tr.update(line=dict(width=2.5, dash="dash"))
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="philippine-sugar-price", figure=fig),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-sugar-btn",
                    n_clicks=0,
                    style={
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
                        "transition": "background-color 0.2s ease-in-out",
                    },
                ),
                dcc.Download(id="download-sugar"),
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])

@callback(
    Output("download-sugar", "data"),
    Input("download-sugar-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_sugar_data(n_clicks):
    df = fetch_philippine_sugar_prices()

    cols = set(df.columns)
    avg_candidates = ["avg_price_per_kilo", "avg_kg_price"]
    med_candidates = ["median_price", "median_kg_price"]

    avg_col = next((c for c in avg_candidates if c in cols), None)
    med_col = next((c for c in med_candidates if c in cols), None)

    return dcc.send_data_frame(
        df[["date", avg_col, med_col]].to_csv,
        "philippine_sugar_price_avg_median.csv",
        index=False
    )