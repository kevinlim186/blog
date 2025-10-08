from dash import Dash, html, dcc, Input, Output, callback
from pages import commitment_of_traders_eur_forcast, german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, german_breakeven_eurusd,telecom_interest_sensitive_stock, wilshire_cumulative_change, wilshire_net_income, us_companies_cashflow_tax, capital_expenditure, interest_rate_differential_eur_usd, free_cash_flow_to_debt, commitment_of_traders, philippine_rice_price, philippine_egg_price, philippine_milk_price, philippine_instant_noodles_price
from cache import cache
from flask import request
import data.queries as dq
import time
import inspect
from flask import Response

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

@cache.memoize()
def free_cash_flow_to_debt_cache():
    return free_cash_flow_to_debt.layout()

@cache.memoize()
def commitment_of_traders_cache():
    return commitment_of_traders.layout()

@cache.memoize()
def commitment_of_traders_eur_forcast_cache():
    return commitment_of_traders_eur_forcast.layout()

@cache.memoize()
def philippine_rice_price_cache():
    return philippine_rice_price.layout()

@cache.memoize()
def philippine_egg_price_cache():
    return philippine_egg_price.layout()

@cache.memoize()
def philippine_milk_price_cache():
    return philippine_milk_price.layout()


# @cache.memoize()
def philippine_instant_noodles_price_cache():
    return philippine_instant_noodles_price.layout()



# Cache database queries.
@app.server.route('/refresh_cache', methods=['POST'])
def refresh_cache():
    import inspect
    import data.queries as dq

    all_funcs = [
        func for name, func in inspect.getmembers(dq, inspect.isfunction)
        if func.__module__ == dq.__name__
    ]

    for func in all_funcs:
        cache.delete_memoized(func)
        try:
            func()
        except Exception as e:
            print(f"⚠️  {func.__name__}() failed: {e}")
        time.sleep(3)

    return Response("Cache has been refreshed", status=200)

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
    elif pathname == '/free-cash-flow-to-debt':
        return free_cash_flow_to_debt_cache()
    elif pathname == '/commitment-of-traders':
        return commitment_of_traders_cache()
    elif pathname == '/commitment-of-traders-eur-forecast':
        return commitment_of_traders_eur_forcast_cache()
    elif pathname == '/philippine-rice-price-history':
        return philippine_rice_price_cache()
    elif pathname == '/philippine-egg-price-history':
        return philippine_egg_price_cache()
    elif pathname == '/philippine-milk-price-history':
        return philippine_milk_price_cache()
    elif pathname == '/philippine-instant-noodles-price-history':
        return philippine_instant_noodles_price_cache()
      
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)