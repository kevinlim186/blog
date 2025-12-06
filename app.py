from dash import Dash, html, dcc, Input, Output, callback
from pages import commitment_of_traders_eur_forcast, german_10_year_breakeven_inflation, german_10_year_inflation_protected_rate,german_10_year_bonds, german_breakeven_eurusd, philippine_instant_3_in_1_coffee_price,telecom_interest_sensitive_stock, wilshire_cumulative_change, wilshire_net_income, us_companies_cashflow_tax, capital_expenditure, interest_rate_differential_eur_usd, free_cash_flow_to_debt, commitment_of_traders, philippine_rice_price, philippine_egg_price, philippine_milk_price, philippine_instant_noodles_price, philippine_cooking_oil_price, philippine_onion_price, philippine_sugar_price, philippine_detergent_powder, philippine_sardines, philippine_milk_alternative
from cache import cache
from flask import request
import data.queries as dq
import time
from datetime import datetime 
import inspect
from flask import Response, json
from flask_cors import CORS
from utils.utility import find_graph
import data.queries as dq
import json

app = Dash(__name__,  suppress_callback_exceptions=True)
CORS(app.server)
cache.init_app(app.server)
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Centralized page → layout cache mapping
PAGE_LAYOUTS = {
    "german-10-year-bonds": german_10_year_bonds,
    "german-10-year-inflation-protected-rate": german_10_year_inflation_protected_rate,
    "german-10-year-breakeven-inflation": german_10_year_breakeven_inflation,
    "wilshire-total-net-income": wilshire_net_income,
    "german-inflation-real-return-spread-eurusd": german_breakeven_eurusd,
    "telecom-interest-sensitive-stock": telecom_interest_sensitive_stock,
    "wilshire-5000-cumulative-change": wilshire_cumulative_change,
    "us-companies-cashflow-tax": us_companies_cashflow_tax,
    "capital-expenditure": capital_expenditure,
    "interest-rate-differential-eur-usd": interest_rate_differential_eur_usd,
    "free-cash-flow-to-debt": free_cash_flow_to_debt,
    "commitment-of-traders": commitment_of_traders,
    "commitment-of_traders-eur-forecast": commitment_of_traders_eur_forcast,
    "philippine-rice-price-history": philippine_rice_price,
    "philippine-egg-price-history": philippine_egg_price,
    "philippine-milk-price-history": philippine_milk_price,
    "philippine-milk-alternative-price-history": philippine_milk_alternative,
    "philippine-instant-noodles-price-history": philippine_instant_noodles_price,
    "philippine-instant-3-in-1-coffee-price-history": philippine_instant_3_in_1_coffee_price,
    "philippine-cooking-oil-price-history": philippine_cooking_oil_price,
    "philippine-onion-price-history": philippine_onion_price,
    "philippine-sugar-history": philippine_sugar_price,
    "philippine-detergent-powder": philippine_detergent_powder,
    "philippine_sardines": philippine_sardines,
}

# Same mapping for API figure extraction
API_FIGURES = PAGE_LAYOUTS


def get_raw_data_for_pathname(pathname):
    """
    Retrieves the raw data DataFrame using the module's get_data() function
    and converts it into the column-oriented dictionary format for the table generator.
    """
    # Use the existing PAGE_LAYOUTS mapping to find the correct module
    module = API_FIGURES.get(pathname) 
    
    if module is None or not hasattr(module, "get_data"):
        # This case should ideally be caught by api_router/api_data, 
        # but handled here for safety.
        return {}

    try:
        # Call the module's get_data() function to get the DataFrame
        df = module.get_data()
    except Exception as e:
        print(f"Error retrieving data for {pathname}: {e}")
        return {}
        
    if df is None or df.empty:
        return {}
    
    # Convert the DataFrame to a dictionary where keys are column names 
    # and values are lists of data points. This is the required format.
    # Note: We return all columns in the DataFrame for completeness in the hidden table.
    return df.to_dict('list')

def generate_invisible_data_table(raw_data, pathname):
    """
    Generates a hidden HTML table containing the raw data for SEO and accessibility.
    
    Args:
        raw_data (dict): Data in {'col_name': [v1, v2, ...]} format.
        pathname (str): The API endpoint path, used for table summary.
    """
    
    if not raw_data:
        return ""
    
    # Determine Headers
    headers = list(raw_data.keys()) 
    
    # Determine number of rows based on the length of the first column list
    try:
        num_rows = len(raw_data[headers[0]])
    except IndexError:
        return "" 

    # Build Table Header
    thead = "<thead><tr>"
    for h in headers:
        thead += f"<th>{h}</th>"
    thead += "</tr></thead>"
    
    # Build Table Body (Iterate rows, then columns)
    tbody = "<tbody>"
    for i in range(num_rows):
        tbody += "<tr>"
        for col in headers:
            # Access the cell value
            cell_value = raw_data[col][i]
            tbody += f"<td>{cell_value}</td>"
        tbody += "</tr>"
    tbody += "</tbody>"
    
    # CSS to hide the table but keep it accessible for screen readers and indexers
    table_style = """
        position: absolute; 
        left: -9999px; 
        top: auto; 
        width: 1px; 
        height: 1px; 
        overflow: hidden;
    """
    
    title = pathname.replace('-', ' ').title()

    table_html = f"""
        <div style="{table_style}">
            <h3>Raw Data for {title}</h3>
            <table summary="Raw data presented in the chart titled {title}">
                {thead}
                {tbody}
            </table>
        </div>
    """
    return table_html

def get_schema_org_jsonld(pathname, title, description, columns, date_modified):
    """
    Generates the JSON-LD script tag for Schema.org Dataset annotation.
    
    Args:
        pathname (str): The API endpoint path.
        title (str): The extracted chart title.
        description (str): The extracted chart description.
        columns (list): List of column names in the dataset.
        date_modified (str): ISO 8601 formatted date string.
    """
    data_format = "CSV"
    # Uses the correct API endpoint for the data download
    data_url = f"https://visualization.yellowplannet.com/api/{pathname}/data" 
    
    schema_data = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "name": f"Dataset for {title}",
        "description": description,
        "url": f"https://visualization.yellowplannet.com/{pathname}", # Link to the main page/chart
        "keywords": title.lower().split() + ["data", "chart", pathname],
        "creator": {
            "@type": "Organization",
            "name": "YellowPlannet.com",
            "url": "http://yellowplannet.com"
        },
        "spatialCoverage": "Global", # Generic setting, adjust if needed
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": data_format,
            "contentUrl": data_url
        },
        "variableMeasured": ", ".join(columns),
        "dateModified": date_modified
    }
    
    json_ld = json.dumps(schema_data, indent=2)

    return f"""
        <script type="application/ld+json">
        {json_ld}
        </script>
    """

@app.server.route('/refresh_cache', methods=['POST'])
def refresh_cache():
    all_funcs = [
        func for name, func in inspect.getmembers(dq, inspect.isfunction)
        if func.__module__ == dq.__name__
    ]

    errors = []

    for func in all_funcs:
        # Clear cache first
        cache.delete_memoized(func)

        try:
            # Execute the function to repopulate cache
            print(f"🔄 Caching → {func.__name__}()")
            func()  
        except Exception as e:
            msg = f"⚠️ {func.__name__} failed: {e}"
            print(msg)
            errors.append(msg)

    # Optional: return response listing which functions failed
    if errors:
        return Response(
            "Cache refreshed with some errors:\n" + "\n".join(errors), 
            status=207
        )

    return Response("Cache has been fully refreshed and rebuilt.", status=200)

@app.server.route('/api/<pathname>')
def api_router(pathname):
    div_id = f"{pathname}-chart"

    if pathname not in API_FIGURES:
        return Response(f"Unknown API endpoint: {pathname}", status=404)

    layout = API_FIGURES[pathname].layout()
    fig = find_graph(layout)

    # Extract title and description from layout
    card = layout.children[0]
    elements = card.children

    extracted_title = ""
    extracted_desc = ""

    for el in elements:
        if isinstance(el, html.H2):
            # Assumes children is a single string or list of strings
            extracted_title = "".join(map(str, el.children)) if isinstance(el.children, list) else str(el.children)
        elif isinstance(el, html.P):
            # Assumes children is a single string or list of strings
            extracted_desc = "".join(map(str, el.children)) if isinstance(el.children, list) else str(el.children)

    if not extracted_title:
        extracted_title = pathname.replace('-', ' ').title()
    if not extracted_desc:
        extracted_desc = "Automatically generated chart embed."

    if fig is None:
        return Response(f"No figure found for {pathname}", status=404)

    figure_json = fig.to_json()

    raw_data = get_raw_data_for_pathname(pathname) 
    table_html = generate_invisible_data_table(raw_data, pathname) 
    columns = list(raw_data.keys()) if raw_data else []
    date_modified = datetime.now().isoformat() 
    json_ld_annotation = get_schema_org_jsonld(
        pathname, 
        extracted_title, 
        extracted_desc, 
        columns, 
        date_modified
    )
    # --- END Preparation ---

    # Build embeddable HTML block
    embed_html = f"""
        {json_ld_annotation}
        
        <div style='
            background: white;
            border-radius: 10px;
            padding: 22px 26px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            margin-bottom: 28px;
            border: 1px solid #eee;
        '>
            <h2 style='
                color: #222;
                margin-bottom: 6px;
                font-weight: 700;
                font-size: 24px;
            '>
                {extracted_title}
            </h2>

            <p style='color:#555; margin-top:0; margin-bottom:16px;'>
                {extracted_desc}
            </p>

            <div id="{div_id}" style="height:100%; width:100%; min-height:460px;"></div>
            <br>
            
            <div style="text-align:center; margin-top:12px;">
                <a 
                    href="https://visualization.yellowplannet.com/api/{pathname}/data"
                    style="
                        /* Professional Palette: Dark Blue/White, Muted Accent */
                        background-color: #243E82; /* Deep Blue Button (Primary Color) */
                        color: white; /* White text for contrast */
                        border: 1px solid #1A316A;
                        padding: 10px 18px;
                        border-radius: 4px;
                        text-decoration: none;
                        font-weight: 600;
                        font-size: 14px;
                        transition: background-color 0.2s;
                        display: inline-flex;
                        align-items: center;
                        /* Subtler shadow */
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
                    "
                    onmouseover="this.style.backgroundColor='#1A316A'" 
                    onmouseout="this.style.backgroundColor='#243E82'"
                >
                    Download Raw Data
                </a>
                
                <p style="
                    color: #777; 
                    font-size: 11px; 
                    margin-top: 10px;
                    margin-bottom: 0;
                ">
                    Data provided by <strong style="color:grey;">yellowplannet.com</strong>
                </p>
            </div>
        </div>
        
        {table_html}

        <script>
        const fig = {figure_json};
        Plotly.newPlot("{div_id}", fig.data, fig.layout, {{responsive: true}});
        
        // Add window resize listener for responsiveness
        const chartId = "{div_id}";
        window.addEventListener('resize', () => {{
            const chartDiv = document.getElementById(chartId);
            if (chartDiv && typeof Plotly !== 'undefined') {{
                Plotly.relayout(chartDiv, {{ autosize: true }});
            }}
        }});
        </script>
        """

    return Response(embed_html, mimetype="text/html")

@app.server.route("/api/<pathname>/data")
def api_data(pathname):
    if pathname not in PAGE_LAYOUTS:
        return Response(f"Unknown dataset: {pathname}", status=404)

    module = PAGE_LAYOUTS[pathname]
    if not hasattr(module, "get_data"):
        return Response(f"Page '{pathname}' has no get_data() function.", status=400)

    df = module.get_data()
    csv_bytes = df.to_csv(index=False)

    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{pathname}.csv"'}
    )

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    clean_path = pathname.lstrip("/")
    if clean_path in PAGE_LAYOUTS:
        return PAGE_LAYOUTS[clean_path].layout()
    return "404 - Page not found"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
