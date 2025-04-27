from dash import Dash, html, dcc, Input, Output, callback
from pages import german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, german_breakeven_eurusd,telecom_interest_sensitive_stock, wilshire_cumulative_change, wilshire_net_income, us_companies_cashflow_tax, capital_expenditure, interest_rate_differential_eur_usd
from cache import cache
from flask import request
from data.queries import *
import time

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

@cache.memoize()
def capital_expenditure_cache():
    return capital_expenditure.layout()

@cache.memoize()
def interest_rate_differential_eur_usd_cache():
    return interest_rate_differential_eur_usd.layout()

# Cache database queries.
@app.server.route('/refresh_cache', methods=['POST'])
def refresh_cache():
    cache.delete_memoized(fetch_inflation_data)
    fetch_inflation_data()
    time.sleep(3)
    cache.delete_memoized(fetch_coporate_america_net_income_to_wilshire)
    fetch_coporate_america_net_income_to_wilshire()
    time.sleep(3)
    cache.delete_memoized(fetch_telecom_interest_sensitive_stock)
    fetch_telecom_interest_sensitive_stock()
    time.sleep(3)
    cache.delete_memoized(get_cash_flow_tax_us_companies)
    get_cash_flow_tax_us_companies()
    cache.delete_memoized(fetch_capital_expenditure_by_industry)
    fetch_capital_expenditure_by_industry()
    cache.delete_memoized(interest_rate_differential_eur_usd_cache)
    interest_rate_differential_eur_usd_cache()


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
    elif pathname == '/capital-expenditure':
        return capital_expenditure_cache()
    elif pathname == '/interest-rate-differential-eur-usd':
        return interest_rate_differential_eur_usd_cache()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)