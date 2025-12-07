from dash import html, dcc, Input, Output, callback
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from data.queries import get_cash_flow_tax_us_companies
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = get_cash_flow_tax_us_companies()
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]

    df_cash = df.groupby(['year', 'category'], as_index=False).agg({'cash_flow': 'sum'})
    df_cash['metric'] = 'Operating Cash Flow'
    df_cash = df_cash.rename(columns={'cash_flow': 'amount'})

    df_tax = df.groupby(['year', 'category'], as_index=False).agg({'taxes_paid': 'sum'})
    df_tax['metric'] = 'Taxes Paid'
    df_tax = df_tax.rename(columns={'taxes_paid': 'amount'})

    df_combined = pd.concat([df_cash, df_tax], ignore_index=True)

    industries = sorted(df_combined['category'].unique())
    n_industries = len(industries)

    fig = make_subplots(
        rows=n_industries, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.03,
        specs=[[{"secondary_y": True}] for _ in range(n_industries)],
        subplot_titles=[industry for industry in industries]
    )

    color_map = {
        'Operating Cash Flow': '#00CC96',
        'Taxes Paid': '#EF553B'
    }

    for idx, industry in enumerate(industries):
        industry_data = df_combined[df_combined['category'] == industry]

        metric_data_cf = industry_data[industry_data['metric'] == 'Operating Cash Flow']
        fig.add_trace(
            go.Scatter(
                x=metric_data_cf['year'],
                y=metric_data_cf['amount'],
                customdata=(metric_data_cf['amount'] / 1e9),
                name="Operating Cash Flow",
                mode='lines+markers',
                line=dict(color=color_map['Operating Cash Flow'], width=2, dash='solid'),
                showlegend=True if idx == 0 else False,
                hovertemplate=f"{industry}<br>%{{x}}<br>Operating CF: $%{{customdata:.2f}}B"
            ),
            row=idx + 1, col=1, secondary_y=False
        )

        metric_data_tax = industry_data[industry_data['metric'] == 'Taxes Paid']
        fig.add_trace(
            go.Scatter(
                x=metric_data_tax['year'],
                y=metric_data_tax['amount'],
                customdata=(metric_data_tax['amount'] / 1e9),
                name="Taxes Paid",
                mode='lines+markers',
                line=dict(color=color_map['Taxes Paid'], width=2, dash='dash'),
                showlegend=True if idx == 0 else False,
                hovertemplate=f"{industry}<br>%{{x}}<br>Taxes Paid: $%{{customdata:.2f}}B"
            ),
            row=idx + 1, col=1, secondary_y=True
        )

        fig.update_yaxes(
            title_text=industry,
            row=idx + 1,
            col=1,
            title_font=dict(size=14, color=THEME_COLORS["text"], family="sans-serif")
        )

    fig.update_annotations(
        font=dict(
            size=12,
            color=THEME_COLORS["text"],
            family="sans-serif",
            weight="bold"
        ),
    )

    fig.update_layout(
        height=350 * n_industries,
        legend=dict(
            orientation='h',
            y=-0.03,
            x=0.5,
            xanchor='center',
            title=''
        ),
        margin=dict(b=80, t=150)
    )

    for i in range(1, n_industries + 1):
        fig.update_xaxes(title_text="Year", row=i, col=1)

    fig.update_yaxes(title_text="Operating Cash Flow ($)", secondary_y=False)
    fig.update_yaxes(title_text="Taxes Paid ($)", secondary_y=True, showgrid=False)

    return themed_card(
        title="US Corporate Operating Cash Flow vs Taxes Paid",
        description="A breakdown by industry showing how operational cash generation compares with taxes paid since 2010.",
        children=[
            dcc.Graph(id="industry-line-subplots", figure=fig),
            html.Div([
                html.Button(
                    "Download CSV",
                    id="download-btn-industry-flow",
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
                        "transition": "background-color 0.2s ease-in-out"
                    }
                ),
                dcc.Download(id="download-data-industry-flow")
            ], style={"textAlign": "center", "marginTop": "20px"})
        ]
    )

@callback(
    Output("download-data-industry-flow", "data"),
    Input("download-btn-industry-flow", "n_clicks"),
    prevent_initial_call=True
)
def download_industry_data(n_clicks):
    df = get_cash_flow_tax_us_companies()
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]

    df_cash = df.groupby(['year', 'category'], as_index=False).agg({'cash_flow': 'sum'})
    df_cash['metric'] = 'Operating Cash Flow'
    df_cash = df_cash.rename(columns={'cash_flow': 'amount'})

    df_tax = df.groupby(['year', 'category'], as_index=False).agg({'taxes_paid': 'sum'})
    df_tax['metric'] = 'Taxes Paid'
    df_tax = df_tax.rename(columns={'taxes_paid': 'amount'})

    df_combined = pd.concat([df_cash, df_tax], ignore_index=True)

    return dcc.send_data_frame(df_combined.to_csv, "industry_operating_cashflow_taxes.csv", index=False)


def get_data():
    df = get_cash_flow_tax_us_companies()
    df = df[(df['year'] >= 2010) & (df['category'] != 'Crypto Assets')]

    df_cash = df.groupby(['year', 'category'], as_index=False).agg({'cash_flow': 'sum'})
    df_cash['metric'] = 'Operating Cash Flow'
    df_cash = df_cash.rename(columns={'cash_flow': 'amount'})

    df_tax = df.groupby(['year', 'category'], as_index=False).agg({'taxes_paid': 'sum'})
    df_tax['metric'] = 'Taxes Paid'
    df_tax = df_tax.rename(columns={'taxes_paid': 'amount'})

    df_combined = pd.concat([df_cash, df_tax], ignore_index=True)
    return df_combined