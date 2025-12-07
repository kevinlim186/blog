from dash import html, dcc, callback, Input, Output
import plotly.express as px
from data.queries import fetch_debt_free_cash_flow_by_industry
from dash.dcc import send_data_frame
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def layout():
    # Fetch and prepare data
    df = fetch_debt_free_cash_flow_by_industry()
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

    industries = sorted(df['category'].unique())
    n_industries = len(industries)

    fig = make_subplots(
        rows=n_industries, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.03,
        subplot_titles=[industry for industry in industries]
    )

    for idx, industry in enumerate(industries):
        industry_data = df[df['category'] == industry]

        fig.add_trace(
            go.Scatter(
                x=industry_data['year'],
                y=industry_data['free_cash_flow_to_long_term_debt'],
                mode='lines+markers',
                name=industry,
                hovertemplate=f"{industry}<br>%{{x}}<br>FCF / Debt: %{{y:.2%}}"
            ),
            row=idx + 1, col=1
        )

        fig.update_yaxes(
            title_text=industry,
            row=idx + 1,
            col=1,
            title_font=dict(size=14, color=THEME_COLORS["text"], family="sans-serif"),
            tickformat=".0%"
        )

    fig.update_layout(
        height=350 * n_industries,
        **CHART_TEMPLATE,
        showlegend=False,
    )

    fig.update_annotations(
        font=dict(
            size=12,
            color=THEME_COLORS["text"],
            family="sans-serif",
            weight="bold"
        )
    )

    for i in range(1, n_industries + 1):
        fig.update_xaxes(title_text="Year", row=i, col=1)

    return themed_card(
        title="Free Cash Flow to Long‑Term Debt Ratio by Industry",
        description="Industry comparison of Free Cash Flow relative to long‑term debt, highlighting sectoral leverage trends.",
        children=[
            dcc.Graph(id="fcf-to-debt-ratio-graph", figure=fig),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-fcf-debt",
                    n_clicks=0,
                    className="black-button"
                ),
                dcc.Download(id="download-fcf-debt")
            ], style={"textAlign": "center", "marginTop": "10px"})
        ]
    )

@callback(
    Output("download-fcf-debt", "data"),
    Input("download-btn-fcf-debt", "n_clicks"),
    prevent_initial_call=True
)
def download_fcf_debt_data(n_clicks):
    df = fetch_debt_free_cash_flow_by_industry()
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
        "free_cash_flow_to_long_term_debt_by_industry.csv",
        index=False
    )

def get_data():
    df = fetch_debt_free_cash_flow_by_industry()
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
    return df
