from dash import html, dcc, callback, Input, Output
import plotly.express as px
from data.queries import fetch_debt_free_cash_flow_by_industry
from dash.dcc import send_data_frame

def layout():
    # Fetch and prepare data
    df = fetch_debt_free_cash_flow_by_industry()
    print(df)
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

    # Create faceted line chart
    fig = px.line(
        df,
        x='year',
        y='free_cash_flow_to_long_term_debt',
        color='category',
        facet_col='category',
        facet_col_wrap=2,  # 👉 only 2 per row
        markers=True,
        labels={
            'year': 'Year',
            'free_cash_flow_to_long_term_debt': 'FCF / Long-Term Debt',
            'category': 'Industry'
        },
        title="Free Cash Flow to Long-Term Debt Ratio by Industry"
    )

    # Clean layout
    fig.update_layout(
        template='plotly_dark',
        title_x=0.01,
        margin=dict(l=0, r=0, t=60, b=50),
        font=dict(color='white', family='Arial'),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        showlegend=False,
    )

    # Format y-axis as percentage
    fig.update_yaxes(tickformat=".0%")

    # Remove repeated y-axis titles
    fig.for_each_yaxis(lambda y: y.update(title=None))

    # Fix facet titles (remove "category=" from text)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # Add ONE y-axis label manually
    fig.add_annotation(
        x=-0.2,  # slight left offset
        y=0.5,    # center vertically
        text="FCF / Long-Term Debt",
        textangle=-90,
        showarrow=False,
        font=dict(size=14, color="white"),
        xref="paper",
        yref="paper",
        xanchor="center",
        yanchor="middle"
    )

    return html.Div([
        html.Div([
            dcc.Graph(id="fcf-to-debt-ratio-graph", figure=fig),
            html.Div([
                html.Button("Download CSV", id="download-btn-fcf-debt", n_clicks=0, className="black-button"),
                dcc.Download(id="download-fcf-debt")
            ], style={"textAlign": "center", "marginTop": "10px"})
        ], className="black-container")
    ])

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