from dash import html, dcc, Input, Output, callback
import plotly.express as px
from data.queries import get_cash_flow_tax_us_companies
import dash
import pandas as pd
import numpy as np


def layout():
    df = get_cash_flow_tax_us_companies()
    df = df[df['year'] >= 2010]
    max_year = df['year'].max()

    # Determine order of industries by total cash flow
    industry_order = df.groupby('category')['cash_flow'].sum().sort_values(ascending=False).index.tolist()
    color_palette = px.colors.qualitative.Prism
    color_map = {cat: color_palette[i % len(color_palette)] for i, cat in enumerate(industry_order)}

    # Format and label
    df_cash = df.groupby(['year', 'category'], as_index=False).agg({'cash_flow': 'sum'})
    df_cash['pct'] = df_cash.groupby('year')['cash_flow'].transform(lambda x: x / x.sum())
    df_cash['label'] = df_cash['pct'].apply(lambda x: f"{x:.0%}" if x > 0.05 else "")
    df_cash['amount'] = df_cash['cash_flow']
    df_cash['metric'] = 'Operating Cash Flow'

    df_tax = df.groupby(['year', 'category'], as_index=False).agg({'taxes_paid': 'sum'})
    df_tax['pct'] = df_tax.groupby('year')['taxes_paid'].transform(lambda x: x / x.sum())
    df_tax['label'] = df_tax['pct'].apply(lambda x: f"{x:.0%}" if x > 0.05 else "")
    df_tax['amount'] = df_tax['taxes_paid']
    df_tax['metric'] = 'Taxes Paid'

    df_combined = pd.concat([
        df_cash[['year', 'category', 'amount', 'label', 'metric']],
        df_tax[['year', 'category', 'amount', 'label', 'metric']]
    ], ignore_index=True)

    # Format hover text
    def format_hover(row):
        if row['amount'] >= 1e12:
            value = f"${row['amount'] / 1e12:.2f}T"
        elif row['amount'] >= 1e9:
            value = f"${row['amount'] / 1e9:.2f}B"
        elif row['amount'] >= 1e6:
            value = f"${row['amount'] / 1e6:.0f}M"
        else:
            value = f"${row['amount']:.0f}"
        return f"{row['category']}<br>{row['year']}: {value} ({row['label']})"

    df_combined['hover'] = df_combined.apply(format_hover, axis=1)

    # Base figure
    fig = px.bar(
        df_combined,
        x='year',
        y='amount',
        color='category',
        facet_row='metric',
        category_orders={'category': industry_order, 'metric': ['Operating Cash Flow', 'Taxes Paid']},
        color_discrete_map=color_map,
        text='label',
        custom_data=['hover'],
        labels={
            'year': 'Year',
            'amount': '',
            'category': 'Industry'
        },
        title=f'Operating Cash Flow and Taxes Paid by U.S. Industry',
        barmode='stack',
        height=900
    )

    fig.update_traces(
        textposition='inside',
        insidetextanchor='middle',
        textfont_size=12,
        hovertemplate='%{customdata[0]}'
    )

    # Add effective cash tax rate in the middle between the two facets
    df_cash = df_combined[df_combined['metric'] == 'Operating Cash Flow']
    df_tax = df_combined[df_combined['metric'] == 'Taxes Paid']

    df_effective = pd.merge(
        df_cash.groupby('year', as_index=False)['amount'].sum().rename(columns={'amount': 'cash_flow'}),
        df_tax.groupby('year', as_index=False)['amount'].sum().rename(columns={'amount': 'taxes_paid'}),
        on='year'
    )

    df_effective['effective_rate'] = df_effective['taxes_paid'] / df_effective['cash_flow']
    df_effective['label'] = df_effective['effective_rate'].apply(lambda x: f"{x:.0%}")


    for metric in ['Operating Cash Flow', 'Taxes Paid']:
        df_total = df_combined[df_combined['metric'] == metric].groupby('year', as_index=False)['amount'].sum()

        # Merge effective tax rate for Taxes Paid
        if metric == 'Taxes Paid':
            df_total = df_total.merge(
                df_effective[['year', 'effective_rate']],
                on='year',
                how='left'
            )

        yref = 'y2' if metric == 'Operating Cash Flow' else 'y'
        value_label_location = max(df_total['amount']) * 1.05

        for _, row in df_total.iterrows():
            value = row['amount']
            year = row['year']

            if metric == 'Operating Cash Flow':
                label = f"${value / 1e9:.1f}B" if value >= 1e9 else f"${value / 1e6:.0f}M"
            else:
                tax_rate = row['effective_rate']
                tax_rate_label = f"tax:{tax_rate:.0%}" if pd.notnull(tax_rate) else "N/A"
                label = (
                    f"${value / 1e9:.1f}B ({tax_rate_label})"
                    if value >= 1e9
                    else f"${value / 1e6:.0f}M ({tax_rate_label})"
                )

            fig.add_annotation(
                x=year,
                y=value_label_location,
                xref='x',
                yref=yref,
                text=label,
                showarrow=False,
                font=dict(color='white', size=13),
                xanchor='center',
                yanchor='bottom',
                textangle=-45
            )



    fig.update_layout(
        template='plotly_dark',
        margin=dict(l=40, r=30, t=60, b=60),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        legend=dict(title='Industry', orientation='h', y=-0.1),
        title=dict(x=0.01, xanchor='left', font=dict(size=22)),
        uniformtext_minsize=10,
        uniformtext_mode='hide'
    )

    fig.update_yaxes(matches=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
    return html.Div([
        html.Div([
            dcc.Graph(id="industry-bar-combined", figure=fig)
        ], className="black-container")
    ])

