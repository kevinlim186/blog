from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from data.queries import fetch_commitment_of_traders
from theme import CHART_TEMPLATE, THEME_COLORS, themed_card


def layout():
    df = fetch_commitment_of_traders().copy()
    df = df.sort_values("report_date")

    df["dealer_net_position"] = (
        df["dealer_positions_long_all"].astype(float)
        - df["dealer_positions_short_all"].astype(float)
    ) / (
        df["dealer_positions_long_all"].astype(float)
        + df["dealer_positions_short_all"].astype(float)
    )

    df["asset_mgr_net_position"] = (
        df["asset_mgr_positions_long_all"].astype(float)
        - df["asset_mgr_positions_short_all"].astype(float)
    ) / (
        df["asset_mgr_positions_long_all"].astype(float)
        + df["asset_mgr_positions_short_all"].astype(float)
    )

    df["lev_money_net_position"] = (
        df["lev_money_positions_long_all"].astype(float)
        - df["lev_money_positions_short_all"].astype(float)
    ) / (
        df["lev_money_positions_long_all"].astype(float)
        + df["lev_money_positions_short_all"].astype(float)
    )

    dimensions = [
        ("asset_mgr_net_position", "Asset Manager Net Position"),
        ("lev_money_net_position", "Leveraged Money Net Position"),
        ("dealer_net_position", "Dealer Net Position"),
    ]

    fig = make_subplots(
        rows=len(dimensions),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=[title for _, title in dimensions],
        specs=[[{"secondary_y": True}] for _ in dimensions],
    )

    for i, (col, title) in enumerate(dimensions, start=1):
        fig.add_trace(
            go.Scatter(
                x=df["report_date"],
                y=df["close"],
                mode="lines",
                name="EUR/USD Close" if i == 1 else None,
                showlegend=i == 1,
                line=dict(width=2.2),
                hovertemplate="%{x}<br>EUR/USD Close: %{y:.4f}<extra></extra>",
            ),
            row=i,
            col=1,
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=df["report_date"],
                y=df[col],
                mode="lines",
                name=title,
                hovertemplate=f"%{{x}}<br>{title}: %{{y:.2f}}<extra></extra>",
            ),
            row=i,
            col=1,
            secondary_y=True,
        )

    fig.update_layout(
        **CHART_TEMPLATE,
        margin_t=180,
        margin_b=20,
        height=250 * len(dimensions),
        autosize=True,
    )

    for i in range(1, len(dimensions) + 1):
        fig.update_yaxes(
            title_text="EUR/USD Close",
            row=i,
            col=1,
            secondary_y=False,
        )
        fig.update_yaxes(
            title_text="Net Position",
            range=[-1, 1],
            row=i,
            col=1,
            secondary_y=True,
        )

    return themed_card(
        title="EUR/USD — COT Net Positions",
        description="EUR/USD close price with normalized net positions by trader category (CFTC COT data).",
        children=[
            dcc.Graph(
                id="cot-net-positions",
                figure=fig,
            ),
            html.Div(
                [
                    html.Button(
                        "Download CSV",
                        id="download-btn-cot-positions",
                        n_clicks=0,
                        style={
                            "backgroundColor": THEME_COLORS["primary"],
                            "color": "#FFF",
                            "padding": "10px 22px",
                            "border": "none",
                            "borderRadius": "6px",
                            "fontWeight": "600",
                            "cursor": "pointer",
                            "fontSize": "14px",
                            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
                        },
                    ),
                    dcc.Download(id="download-cot-positions"),
                ],
                style={"textAlign": "right", "marginTop": "12px"},
            ),
        ],
    )



def get_data():
    df = fetch_commitment_of_traders().copy()

    df["dealer_net_position"] = (
        df["dealer_positions_long_all"].astype(float)
        - df["dealer_positions_short_all"].astype(float)
    ) / (
        df["dealer_positions_long_all"].astype(float)
        + df["dealer_positions_short_all"].astype(float)
    )

    df["asset_mgr_net_position"] = (
        df["asset_mgr_positions_long_all"].astype(float)
        - df["asset_mgr_positions_short_all"].astype(float)
    ) / (
        df["asset_mgr_positions_long_all"].astype(float)
        + df["asset_mgr_positions_short_all"].astype(float)
    )

    df["lev_money_net_position"] = (
        df["lev_money_positions_long_all"].astype(float)
        - df["lev_money_positions_short_all"].astype(float)
    ) / (
        df["lev_money_positions_long_all"].astype(float)
        + df["lev_money_positions_short_all"].astype(float)
    )

    return df


def get_meta_data():
    return {
        "spatial_coverage": [
            {"@type": "Place", "name": "Euro Area / United States"}
        ],
        "url": "https://yellowplannet.com/can-cot-data-predict-the-eur-usd-a-data-driven-faq-on-positioning-reversals-and-trading-models/",
    }
