from dash import Dash, html, dcc, Input, Output, callback
from pages import german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, sp500_total_revenue, german_breakeven_eurusd,telecom_interest_sensitive_stock, sp500_cumulative_change
from flask_caching import Cache
from flask import request


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

@cache.memoize()
def german_breakeven_eurusd_cache():
    return german_breakeven_eurusd.layout()

@cache.memoize()
def telecom_interest_sensitive_stock_cache():
    return telecom_interest_sensitive_stock.layout()

@cache.memoize()
def sp500_cumulative_change_cache():
    return sp500_cumulative_change.layout()



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
    cache.delete_memoized(german_breakeven_eurusd_cache)
    german_breakeven_eurusd_cache()
    cache.delete_memoized(telecom_interest_sensitive_stock_cache)
    telecom_interest_sensitive_stock_cache()
    cache.delete_memoized(sp500_cumulative_change_cache)
    sp500_cumulative_change_cache()
    
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
    elif pathname == '/german-inflation-real-return-spread-eurusd':
        return german_breakeven_eurusd_cache()
    elif pathname == '/telecom-interest-sensitive-stock':
        return telecom_interest_sensitive_stock_cache()
    elif pathname == '/sp500-cumulative-change':
        return sp500_cumulative_change_cache()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)