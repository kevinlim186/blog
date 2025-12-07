from dash import html, dcc, Input, Output, callback
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from data.queries import fetch_commitment_of_traders
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card

def layout():
    df = fetch_commitment_of_traders()

    df['dealer_net_position'] = (df['dealer_positions_long_all'].astype(float)-df['dealer_positions_short_all'].astype(float))/(df['dealer_positions_long_all'].astype(float)+df['dealer_positions_short_all'].astype(float))
    df['asset_mgr_net_position'] = ( df['asset_mgr_positions_long_all'].astype(float) - df['asset_mgr_positions_short_all'].astype(float)) / ( df['asset_mgr_positions_long_all'].astype(float) + df['asset_mgr_positions_short_all'].astype(float))
    df['lev_money_net_position'] = (df['lev_money_positions_long_all'].astype(float)-df['lev_money_positions_short_all'].astype(float))/(df['lev_money_positions_long_all'].astype(float)+df['lev_money_positions_short_all'].astype(float))
    df['total_net_position']= (df['dealer_net_position']+df['asset_mgr_net_position']+df['lev_money_net_position'])/3

    # Each tuple: (column, title)
    dimensions = [
        ("asset_mgr_net_position", "Asset Manager Net Position"),
        ("lev_money_net_position", "Leveraged Money Net Position"),
        ("dealer_net_position", "Dealer Net Position")
    ]

    # Enable secondary_y for each subplot
    fig = make_subplots(
        rows=len(dimensions), cols=1,
        shared_xaxes=True,
        vertical_spacing=0.18,  # increased vertical spacing between subplots
        subplot_titles=[title for _, title in dimensions],
        specs=[[{"secondary_y": True}] for _ in dimensions]
    )

    for i, (col, title) in enumerate(dimensions, start=1):
        # Plot close price on primary y-axis
        fig.add_trace(
            go.Scatter(
                x=df["report_date"],
                y=df["close"],
                mode='lines',
                name="EUR/USD Close" if i == 1 else None,
                showlegend=(i == 1),
                line=dict(color='white', width=2, dash='solid'),
                hovertemplate="%{x}<br>EUR/USD Close: %{y:.4f}"
            ),
            row=i, col=1, secondary_y=False
        )
        # Plot net position on secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=df["report_date"],
                y=df[col],
                mode='lines',
                name=title,
                hovertemplate=f"%{{x}}<br>{title}: %{{y:.2f}}"
            ),
            row=i, col=1, secondary_y=True
        )

    fig.update_layout(
        height=300 * len(dimensions),
        template='plotly_dark',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font=dict(color='white', family='Arial'),
        title=dict(
            text="EUR/USD Close and Net Positions by Trader Category",
            x=0.01,
            font=dict(
                family="Arial Black",
                size=22,
                color="white"
            )
        ),
        margin=dict(t=200, l=50, r=50, b=80),  # increased top margin for more space below title
        hovermode='x unified',
    )

    for i, (_, title) in enumerate(dimensions, start=1):
        fig.update_xaxes(title_text="Date", row=i, col=1)
        fig.update_yaxes(title_text="EUR/USD Close", row=i, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Net Position", row=i, col=1, secondary_y=True, range=[-1, 1])

    return html.Div([
        dcc.Graph(id="net-interest-positions", figure=fig)
    ])

@callback(
    Output("download-data-cot-positions", "data"),
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

    return dcc.send_data_frame(df_combined.to_csv, "cot_net_positions.csv", index=False)