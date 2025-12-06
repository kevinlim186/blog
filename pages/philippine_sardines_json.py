import plotly.graph_objects as go
from data.queries import philippine_sardines

def get_figure():
    df = philippine_sardines()
    df = df.sort_values(by="date")

    # Column validation
    expected_cols = {"date", "mean_price", "median_price", "sampled_skus"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Main price line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["mean_price"],
        mode="lines",
        name="Average (PHP per 155g)",
        line=dict(width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["median_price"],
        mode="lines",
        name="Median (PHP per 155g)",
        line=dict(width=2.5, dash="dash")
    ))

    # ✅ Add sampled SKU count as contextual secondary axis
    fig.add_trace(go.Bar(
        x=df["date"],
        y=df["sampled_skus"],
        name="Sampled SKUs",
        opacity=0.25,
        marker_color="#AAAAAA",
        yaxis="y2",
        hovertemplate="SKUs sampled: %{y}<extra></extra>"
    ))

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font=dict(color="white", family="Arial"),
        title=dict(
            text="Philippine Sardines Prices — Standardized to 155g",
            x=0.01,
            xanchor="left",
            font=dict(size=26, family="Open Sans", color="white"),
        ),
        height=500,
        margin=dict(l=30, r=30, t=100, b=50),
        hovermode="x unified",
        yaxis=dict(
            title="Price (PHP per 155g)",
            gridcolor="#333"
        ),
        yaxis2=dict(
            title="Sample Size (SKUs)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        )
    )

    return fig
