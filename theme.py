from dash import html

THEME_COLORS = {
    "background": "#F5F7FA",
    "card": "#FFFFFF",
    "primary": "#005BBB",          # Deep professional blue (main brand color)

    "secondary": "#2F80ED",        # Softer blue for secondary lines
    "accent": "#F2C94C",           # Gold accent (for EUR/USD or special lines)

    "text": "#1A1A1A",
    "textMuted": "#5A5A5A",

    "grid": "#D7DDE5",

    "button": "#005BBB",           # Matches primary
    "buttonText": "#FFFFFF"        # White text on blue button
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

    # Increased bottom margin so footer doesn't collide with legend
    "margin": dict(l=50, r=50, t=120, b=70),

    "hovermode": "x unified",
    "legend": dict(
        orientation="h",
        y=-0.25,
        x=0.0,
        xanchor="left",
        font=dict(size=14),
    ),

}
def themed_card(children, title=None, description=None, style=None):
    base = {
        "backgroundColor": THEME_COLORS["card"],
        "padding": "20px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
        "marginBottom": "25px",
        "border": "1px solid #E5E9F0"
    }
    if style:
        base.update(style)

    graph = None
    child_list = children if isinstance(children, (list, tuple)) else [children]

    for c in child_list:
        if hasattr(c, "figure"):
            graph = c
            break
    if  (title or description):
        existing = list(graph.figure.layout.annotations) if graph.figure.layout.annotations else []
        annotations = existing.copy()

        if title:
            extracted_desc = description if description else ""
            full_title = title
            if description:
                full_title = (
                    f"{title}"
                    f"<br><span style='font-size:14px; color:{THEME_COLORS['textMuted']};"
                    f" font-family:sans-serif;'>{description} <br><b>Data provided by <b>yellowplannet.com</b></span>"
                )

            graph.figure.update_layout(
                title=dict(
                    text=full_title,
                    x=0.05,
                    xanchor="left",
                    font=dict(size=20, color=THEME_COLORS["text"], family="sans-serif"), 
                    
                )
            )
            
        safe_l = graph.figure.layout.margin.l or 0
        safe_r = graph.figure.layout.margin.r or 0
        safe_t = graph.figure.layout.margin.t or 0
        safe_b = graph.figure.layout.margin.b or 0

        graph.figure.update_layout(
            margin=dict(
                l=safe_l,
                r=safe_r,
                t=safe_t,
                b=safe_b,
            )
        )

    return html.Div(children, style=base)