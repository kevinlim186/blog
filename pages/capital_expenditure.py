from dash import html, dcc, Input, Output, callback
import plotly.express as px
from data.queries import fetch_capital_expenditure_by_industry
import plotly.graph_objects as go
from dash.dcc import send_data_frame
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

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
        **CHART_TEMPLATE,
    )

    return themed_card(
        title="Inflation-Adjusted Capital Expenditures",
        description="Industry-level capital expenditure trends adjusted for inflation, measured in billions.",
        children=[
            dcc.Graph(
                id="inflation-adjusted-capex-graph",
                figure=fig,
                style={"height": "460px"}
            ),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-inflation-adjusted-capex",
                    n_clicks=0,
                    style={
                        "backgroundColor": THEME_COLORS["primary"],
                        "color": "#000",
                        "padding": "10px 22px",
                        "border": "none",
                        "borderRadius": "6px",
                        "fontWeight": "600",
                        "cursor": "pointer",
                        "fontSize": "14px",
                        "boxShadow": "0 2px 6px rgba(255,204,0,.45)"
                    }
                ),
                dcc.Download(id="download-inflation-adjusted-capex")
            ], style={"textAlign": "right", "marginTop": "12px"})
        ]
    )

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

def get_data():
    df = fetch_capital_expenditure_by_industry()
    df = df.sort_values(by=['year', 'category'])

    # Filter and reshape
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]
    df['capital_expenditure_b'] = df['inflation_adjusted_capital_expenditure'] / 1e9  
    return df


def get_meta_data():
    res = {}
    res['spatial_coverage'] =[
        { "@type": "Place", "name": "United States" },
        ]
    
    res['url'] = 'https://yellowplannet.com/capital-expenditures-by-industry-a-decade-of-shifting-investment-strategies/'

    return res 