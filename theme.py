from dash import html

THEME_COLORS = {
    "background": "#F5F7FA",
    "card": "#FFFFFF",
    "primary": "#005BBB",   # Professional blue (similar to Bloomberg / TradingEconomics)
    "text": "#1A1A1A",
    "grid": "#D7DDE5",
}

THEME_FONT = {
    "family": "Inter, Open Sans, Arial",
    "color": THEME_COLORS["text"]
}

CHART_TEMPLATE = {
    "template": "simple_white",
    "paper_bgcolor": THEME_COLORS["card"],
    "plot_bgcolor": THEME_COLORS["card"],
    "font": THEME_FONT,
    "margin": dict(l=40, r=40, t=80, b=40),
    "hovermode": "x unified",
}

def themed_card(children, style=None):
    base = {
        "backgroundColor": THEME_COLORS["card"],
        "padding": "20px",
        "borderRadius": "8px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
        "marginBottom": "25px",
        "border": "1px solid #E5E9F0"
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)