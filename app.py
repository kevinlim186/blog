from dash import Dash, html, dcc, Input, Output, callback
from pages import german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, sp500_total_revenue
from flask_caching import Cache



app = Dash(__name__,  suppress_callback_exceptions=True)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'SimpleCache',  # or 'filesystem' for larger data
    'CACHE_DEFAULT_TIMEOUT': 60 * 60  * 24 # 1 hour
})

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Cache the layouts
@cache.memoize()
def german_10_year_bonds_cache():
    return german_10_year_bonds.layout()

@cache.memoize()
def german_10_year_inflation_protected_rate_cache():
    return german_10_year_inflation_protected_rate.layout()

@cache.memoize()
def german_10_year_breakeven_inflation_cache():
    return german_10_year_breakeven_inflation.layout()

@cache.memoize()
def sp500_total_revenue_cache():
    return sp500_total_revenue.layout()


from flask import request

@app.server.route('/refresh_cache', methods=['POST'])
def refresh_cache():
    cache.delete_memoized(german_10_year_bonds_cache)
    german_10_year_bonds_cache()
    cache.delete_memoized(german_10_year_inflation_protected_rate_cache)
    german_10_year_inflation_protected_rate_cache()
    cache.delete_memoized(german_10_year_breakeven_inflation_cache)
    german_10_year_breakeven_inflation_cache()
    cache.delete_memoized(sp500_total_revenue_cache)
    sp500_total_revenue_cache()
    return "Cache has been refreshed", 200

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/german-10-year-bonds':
        return german_10_year_bonds_cache()
    elif pathname == '/german-10-year-inflation-protected-rate':
        return german_10_year_inflation_protected_rate_cache()
    elif pathname == '/german-10-year-breakeven-inflation':
        return german_10_year_breakeven_inflation_cache()
    elif pathname == '/sp500-total-revenue':
        return sp500_total_revenue_cache()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)