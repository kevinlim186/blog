from dash import Dash, html, dcc, Input, Output, callback
from pages import german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, german_breakeven_eurusd,telecom_interest_sensitive_stock, wilshire_cumulative_change, wilshire_net_income, us_companies_cashflow_tax
from cache import cache
from flask import request
from data.queries import *

app = Dash(__name__,  suppress_callback_exceptions=True)
cache.init_app(app.server) 
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
def wilshire_net_income_cache():
    return wilshire_net_income.layout()

@cache.memoize()
def german_breakeven_eurusd_cache():
    return german_breakeven_eurusd.layout()

@cache.memoize()
def telecom_interest_sensitive_stock_cache():
    return telecom_interest_sensitive_stock.layout()

@cache.memoize()
def wilshire_cumulative_change_cache():
    return wilshire_cumulative_change.layout()

@cache.memoize()
def us_companies_cashflow_tax_cache():
    return us_companies_cashflow_tax.layout()



@app.server.route('/refresh_cache', methods=['POST'])
def refresh_cache():
    cache.delete_memoized(german_10_year_bonds_cache)
    german_10_year_bonds_cache()
    cache.delete_memoized(german_10_year_inflation_protected_rate_cache)
    german_10_year_inflation_protected_rate_cache()
    cache.delete_memoized(german_10_year_breakeven_inflation_cache)
    german_10_year_breakeven_inflation_cache()
    cache.delete_memoized(wilshire_net_income_cache)
    wilshire_net_income_cache()
    cache.delete_memoized(german_breakeven_eurusd_cache)
    german_breakeven_eurusd_cache()
    cache.delete_memoized(telecom_interest_sensitive_stock_cache)
    telecom_interest_sensitive_stock_cache()
    cache.delete_memoized(wilshire_cumulative_change_cache)
    wilshire_cumulative_change_cache()
    cache.delete_memoized(us_companies_cashflow_tax_cache)
    us_companies_cashflow_tax_cache()
    
    return "Cache has been refreshed", 200

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/german-10-year-bonds':
        return german_10_year_bonds_cache()
    elif pathname == '/german-10-year-inflation-protected-rate':
        return german_10_year_inflation_protected_rate_cache()
    elif pathname == '/german-10-year-breakeven-inflation':
        return german_10_year_breakeven_inflation_cache()
    elif pathname == '/wilshire-total-net-income':
        return wilshire_net_income_cache()
    elif pathname == '/german-inflation-real-return-spread-eurusd':
        return german_breakeven_eurusd_cache()
    elif pathname == '/telecom-interest-sensitive-stock':
        return telecom_interest_sensitive_stock_cache()
    elif pathname == '/wilshire-5000-cumulative-change':
        return wilshire_cumulative_change_cache()
    elif pathname == '/us-companies-cashflow-tax':
        return us_companies_cashflow_tax_cache()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)