from dash import html, dcc, callback, Input, Output
import plotly.express as px
from data.queries import fetch_capital_expenditure_by_industry
import plotly.graph_objects as go
from dash.dcc import send_data_frame

def layout():
    df = fetch_capital_expenditure_by_industry()
    df = df.sort_values(by=['year', 'category'])

    # Filter and reshape
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]
    df['capital_expenditure_b'] = df['inflation_adjusted_capital_expenditure'] / 1e9  # now use inflation-adjusted!

    rename_map = {
        'Industrial Applications and Services': 'Industrial',
        'Energy & Transportation': 'Energy/Transport',
        'Real Estate & Construction': 'Real Estate',
        'Trade & Services': 'Trade',
        'Life Sciences': 'LifeSci',
        'Technology': 'Tech',
        'Manufacturing': 'Mfg',
        'Finance': 'Finance'
    }
    df['category'] = df['category'].map(rename_map).fillna(df['category'])

    # Create line figure
    fig = px.line(
        df,
        x='year',
        y='capital_expenditure_b',
        color='category',
        labels={
            'year': 'Year',
            'capital_expenditure_b': 'Inflation-Adjusted CapEx (B)',
            'category': 'Industry'
        },
        markers=True
    )

    fig.update_layout(
        template='plotly_dark',
        title="Inflation-Adjusted Capital Expenditures by Industry (in Billions)",
        title_x=0.01,
        margin=dict(l=60, r=30, t=60, b=80),
        font=dict(color='white', family='Arial'),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        legend=dict(
            orientation='h',
            y=-0.3,
            x=0.5,
            xanchor='center'
        )
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="inflation-adjusted-capex-graph", figure=fig),
            html.Div([
                html.Button("Download CSV", id="download-btn-inflation-adjusted-capex", n_clicks=0, style={
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
                dcc.Download(id="download-inflation-adjusted-capex")
            ], style={"textAlign": "center"})
        ], className="black-container")
    ])

@callback(
    Output("download-inflation-adjusted-capex", "data"),
    Input("download-btn-inflation-adjusted-capex", "n_clicks"),
    prevent_initial_call=True
)
def download_inflation_adjusted_capex_data(n_clicks):
    df = fetch_capital_expenditure_by_industry()
    df = df.sort_values(by=['year', 'category'])
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]

    rename_map = {
        'Industrial Applications and Services': 'Industrial',
        'Energy & Transportation': 'Energy/Transport',
        'Real Estate & Construction': 'Real Estate',
        'Trade & Services': 'Trade',
        'Life Sciences': 'LifeSci',
        'Technology': 'Tech',
        'Manufacturing': 'Mfg',
        'Finance': 'Finance'
    }
    df['category'] = df['category'].map(rename_map).fillna(df['category'])

    return send_data_frame(
        df.to_csv,
        "inflation_adjusted_capital_expenditure_data.csv",
        index=False
    )