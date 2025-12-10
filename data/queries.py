from .db_client import get_clickhouse_client
from cache import cache

@cache.memoize()
def fetch_inflation_data():
    client = get_clickhouse_client()
    query = """
            WITH bonds_data AS (
            select *
            from (
                SELECT 
                    bond_type, ticker, date, isin, issue_date, maturity, coupon, close
                FROM trading.asset_prices a
                INNER JOIN (
                    SELECT coupon, date issue_date, isin, bond_type, maturity
                    FROM trading.bonds 
                    WHERE 
                        isin LIKE 'DE%'
                        /* AND maturity >= today() */  
                    ORDER BY version DESC 
                    LIMIT 1 BY isin
                ) t  ON t.isin = a.ticker
                order by version desc 
                limit 1 by ticker, date)
            where  close>0
            ),

            ytm_data_bond AS (
                SELECT 
                    bond_type,
                    ticker,
                    isin,
                    date,
                    maturity,
                    coupon AS coupon_rate,  
                    close AS bond_price,
                    dateDiff('year', date, maturity) AS years_to_maturity,
                    
                    -- Approximate YTM Formula
                    ( (coupon * 100) + ((100 - close) / dateDiff('year', date, maturity)) ) 
                    / ((100 + close) / 2) AS yield_to_maturity
                FROM bonds_data
                WHERE coupon > 0 
                AND bond_type IN ('Bond')
                and years_to_maturity>0
            ),

            ytm_bond_interpolation AS (
                SELECT 
                    date,
                    argMin(yield_to_maturity, years_to_maturity) AS lower_yield,
                    argMin(years_to_maturity, years_to_maturity) AS lower_maturity,
                    argMax(yield_to_maturity, years_to_maturity ) AS upper_yield,
                    argMax(years_to_maturity, years_to_maturity) AS upper_maturity
                FROM ytm_data_bond
                where yield_to_maturity is not null 
                GROUP BY date
            ), 

            ytm_data_bond_interpolated AS (
            select 
                date, 
                avg(interpolated_yield_bond) interpolated_yield_bond
            from (
                SELECT 
                    date,
                    years_to_maturity,
                    -- Use the exact 10Y yield if available, otherwise interpolate
                    CASE 
                        when years_to_maturity=10 then yield_to_maturity
                        else yield_to_maturity + ((upper_yield - lower_yield) * (10 - years_to_maturity)) / NULLIF(upper_maturity - lower_maturity, 0)
                    END AS interpolated_yield_bond
                FROM ytm_bond_interpolation
                INNER JOIN ytm_data_bond ON ytm_data_bond.date = ytm_bond_interpolation.date
                )
            group by 
                date
            ),
            ytm_data_tips AS (
                SELECT 
                    bond_type,
                    ticker,
                    isin,
                    date,
                    maturity,
                    coupon AS coupon_rate,  
                    close AS bond_price,
                    dateDiff('year', date, maturity) AS years_to_maturity,
                    
                    -- Approximate YTM Formula
                    ( (coupon * 100) + ((100 - close) / dateDiff('year', date, maturity)) ) 
                    / ((100 + close) / 2) AS yield_to_maturity
                FROM bonds_data 
                WHERE coupon > 0
                AND bond_type IN ('TIPS')
                and years_to_maturity>0
            ),

            ytm_tips_interpolation AS (

                SELECT 
                    date,
                    argMin(yield_to_maturity, years_to_maturity) AS lower_yield,
                    argMin(years_to_maturity, years_to_maturity) AS lower_maturity,
                    argMax(yield_to_maturity, years_to_maturity ) AS upper_yield,
                    argMax(years_to_maturity, years_to_maturity) AS upper_maturity

                FROM ytm_data_tips
                where yield_to_maturity is not null  
                GROUP BY date
            ), 

            ytm_data_tips_interpolated AS (
            select 
            date, 
            avg(interpolated_yield_tips) interpolated_yield_tips
            from (
            SELECT 
                date,
                years_to_maturity,
                -- Use the exact 10Y yield if available, otherwise interpolate
                    CASE 
                    when years_to_maturity=10 then yield_to_maturity
                    else yield_to_maturity + ((upper_yield - lower_yield) * (10 - years_to_maturity)) / NULLIF(upper_maturity - lower_maturity, 0)
                    END AS interpolated_yield_tips
            FROM ytm_tips_interpolation
            INNER JOIN ytm_data_tips ON ytm_data_tips.date = ytm_tips_interpolation.date
            )
            group by 
            date
            ),
            german_bonds as (

            SELECT 
                ytm_data_tips_interpolated.date date, 
                interpolated_yield_bond, 
                interpolated_yield_tips, 
                interpolated_yield_bond - interpolated_yield_tips AS interpolated_german_breakeven_inflation
            FROM ytm_data_tips_interpolated
            INNER JOIN ytm_data_bond_interpolated 
            ON ytm_data_tips_interpolated.date = ytm_data_bond_interpolated.date
            ), 
            us_inflation as (
            select 
            date,
            avg(case when attribute='us_10_year_breakeven_inflation_rate' then value end) us_10_year_breakeven_inflation_rate,
            avg(case when attribute='us_ten_year_interest' then value end) us_ten_year_interest
            from (
            select *
            from trading.economic_calendar ec 
            where attribute in ('us_10_year_breakeven_inflation_rate', 'us_ten_year_interest')
            order by version desc 
            limit 1 by date,attribute )
            group by date
            ),
            eur_usd as (
            SELECT 
            date, 
            close eur_usd_fx
            from trading.asset_prices 
            where 
            ticker='eurusd'
            order by version desc 
            limit 1 by date
            )


            select 
                german_bonds.date date, 
                interpolated_german_breakeven_inflation*100 interpolated_german_breakeven_inflation, 
                us_10_year_breakeven_inflation_rate us_breakeven_inflation,  
                us_ten_year_interest-us_10_year_breakeven_inflation_rate us_implied_tips, 
                eur_usd_fx,     
                interpolated_yield_bond*100 interpolated_yield_bond,  
                interpolated_yield_tips*100 interpolated_yield_tips, 
                us_ten_year_interest,
                interpolated_german_breakeven_inflation-us_10_year_breakeven_inflation_rate breakeven_inflation_spread, 
                interpolated_yield_tips-us_implied_tips real_return_spread
            from german_bonds
            inner join us_inflation on (us_inflation.date=german_bonds.date)
            inner join eur_usd on (eur_usd.date=german_bonds.date)
            where date>='2010-01-01'
            order by date asc
    """
    return client.query_df(query)

@cache.memoize()
def fetch_coporate_america_net_income_to_wilshire():
    client = get_clickhouse_client()
    query = """
        with base as (
            SELECT 
                entity,
                date,
                metric / (dateDiff('day', start, end) + 1) AS allocated_metric
            FROM (
                SELECT 
                    start,
                    end,
                    case when dimension='Investment Income, Interest and Dividend' then  -metric else metric end metric,
                    entity,
                    addDays(start, number) AS date
                FROM (
                    SELECT 
                        start, 
                        end, 
                        dimension,
                        metric, 
                        entity
                    FROM trading.equity_fundamental 
                    WHERE 
                        (
                            dimension LIKE 'Net Income (Loss) Attributable to Parent'
                            or 
                            dimension LIKE 'Investment Income, Interest and Dividend'
                        )	
                        AND start >= '2007-01-01'
                        AND form = '10-K'
                        AND dateDiff('day', start, end) > 350
                    
                    ORDER BY created_at DESC, filed DESC 
                    LIMIT 1 BY start, end, entity, dimension
                ) AS input
                ARRAY JOIN range(CAST(dateDiff('day', start, end) + 1 AS UInt64)) AS number
            
            )
            where toYear(date)<=toYear(today())-2 and toYear(date)>=2010
            ORDER BY date
            ),
            income as (
            select 
                toYear(date) dt, 
                count(distinct entity) entities,
                sum(allocated_metric) total_net_income, 
                sum(allocated_metric)/entities avg_revenue_per_entity
            from base
            group by dt),

            prices as (
            select 
                date, cik, close, volume
            from trading.asset_prices 
            where 
                ticker like '^W5000'
                and date>='2010-01-01'
            order by version desc limit 1 by date),

            weighted_price as (
            select 
                toYear(date) dt, 
                avg(close) avg_price
            from prices
            group by 
                dt
            )

            select income.dt year, total_net_income, avg_price
            from income
            left join weighted_price on income.dt = weighted_price.dt

    """
    return client.query_df(query)

@cache.memoize()
def fetch_telecom_interest_sensitive_stock():
    client = get_clickhouse_client()
    query = """
    WITH stocks AS (
        SELECT 
            date, 
            CASE WHEN ticker = '^GSPC' THEN 'SP500' ELSE ticker END AS ticker, 
            close adj_close
        FROM trading.asset_prices 
        WHERE asset_prices.ticker IN ('T', 'VZ', 'CCOI', '^GSPC')
            AND date >= today()- interval 1 year
            -- AND date between '2019-04-01' and '2020-08-31'
        ORDER BY version DESC 
        LIMIT 1 BY ticker, date
        ),

        start_value AS (
        SELECT 
            ticker, 
            argMin(adj_close, date) first_value
        FROM stocks
        group by ticker
        ),

        cumulative_gain as (

        SELECT 
        date, ticker, adj_close/first_value-1 cumulative_gain
        FROM stocks
        LEFT JOIN start_value ON start_value.ticker=stocks.ticker
        )

        SELECT 
        date, value interest_rates, ticker, cumulative_gain*100 cumulative_gain
        from trading.economic_calendar 
        left join cumulative_gain on trading.economic_calendar.date = cumulative_gain.date
        where 
        (attribute ='us_twenty_year_interest')
        and value>0
        and ticker!=''
        -- or attribute='us_consumer_price_index_all_urban_consumers'
        order by date
    """
    return client.query_df(query)

@cache.memoize()
def get_cash_flow_tax_us_companies():
    client = get_clickhouse_client()
    query = '''
        with base as (
        SELECT 
            entity,
            date,
            dimension,
            id,
            metric / (dateDiff('day', start, end) + 1) AS allocated_metric
        FROM (
            SELECT 
                start,
                end,
                dimension,
                metric,
                entity,
                id,
                addDays(start, number) AS date
            FROM (
                SELECT 
                    start, 
                    end, 
                    dimension,
                    metric, 
                    entity, 
                    id
                FROM trading.equity_fundamental 
                WHERE 
                    (
                        dimension LIKE 'Income Taxes Paid, Net'
                        or 
                        dimension LIKE '%Net Cash Provided by (Used in) Operating Activities, Continuing Operations%'
                        or 
                        dimension like  'Net Cash Provided by (Used in) Operating Activities'
                        or 
                        dimension like 'Income Taxes Paid'
                    )	
                    AND id !='707605' -- faulty data
                    AND start >= '2007-01-01'
                    AND form = '10-K'
                    AND dateDiff('day', start, end) > 350
                ORDER BY created_at DESC, filed DESC 
                LIMIT 1 BY start, end, entity, dimension
            ) AS input
            ARRAY JOIN range(CAST(dateDiff('day', start, end) + 1 AS UInt64)) AS number
        
        )
        where toYear(date)<=toYear(today())-2 and toYear(date)>=2010
        ORDER BY date
        ),

        orgs as (
        select 
            cik, ownerOrg, category
        from trading.equity_companies
        order by created_at 
        limit 1 by cik 

        ),

        summary as (

        select 
            toStartOfYear(date) dt,
            id,
            dimension,
            sum(allocated_metric) allocated_metric
        from base
        group by dt, dimension, id
        )

        select 
            toYear(dt) year,
            replaceRegexpOne(ownerOrg, '^\\d+\\s*', '') category, 
            sumIf(allocated_metric, dimension like '%Income Taxes Paid%') taxes_paid,
            sumIf(allocated_metric, dimension like '%Operating Activities%') cash_flow, 
            taxes_paid/cash_flow tax_rate
        from summary 
        left join orgs on summary.id=orgs.cik
        where category!=''
        group by 
            year, 
            category

    '''
    
    return client.query_df(query)


@cache.memoize()
def fetch_capital_expenditure_by_industry():
    client = get_clickhouse_client()
    query = """
    with base as (
        SELECT 
            entity,
            date,
            dimension,
            id,
            metric / (dateDiff('day', start, end) + 1) AS allocated_metric
        FROM (
            SELECT 
                start,
                end,
                dimension,
                metric,
                entity,
                id,
                addDays(start, number) AS date
            FROM (
                SELECT 
                    start, 
                    end, 
                    dimension,
                    metric, 
                    entity, 
                    id
                FROM trading.equity_fundamental 
                WHERE 
                    (
                        dimension= 'Payments to Acquire Property, Plant, and Equipment'
                        or 
                        dimension like 'Payments to Acquire Intangible Assets'
                    )	
                    AND id !='707605' -- faulty data
                    AND start >= '2009-01-01'
                    AND form = '10-K'
                    AND dateDiff('day', start, end) > 350
                ORDER BY created_at DESC, filed DESC 
                LIMIT 1 BY start, end, entity, dimension
            ) AS input
            ARRAY JOIN range(CAST(dateDiff('day', start, end) + 1 AS UInt64)) AS number
        
        )
        where toYear(date)<=toYear(today())-2 and toYear(date)>=2010
        ORDER BY date
        ),
        
        inflation_adjustment as (
	        select 
				year, 
				value,
				exp(cumulative_multiplier) inflation_adjustment
			from (
			SELECT 
			    toYear(date) AS year, 
			    value / 100 AS value,
			    sum(log(1 + value )) OVER (ORDER BY date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_multiplier
			FROM (
			    SELECT *
			    FROM trading.economic_calendar
			    WHERE 
			        attribute = 'us_inflation_yearly'
			        AND toYear(date) >= 2009
			    ORDER BY version DESC
			    LIMIT 1 BY date, attribute
			))
			ORDER BY year ASC
        
        ),

        orgs as (
        select 
            cik, ownerOrg, category
        from trading.equity_companies
        order by created_at 
        limit 1 by cik 

        ),

        summary as (

        select 
            toStartOfYear(date) dt,
            id,
            dimension,
            sum(allocated_metric) allocated_metric
        from base
        group by dt, dimension, id
        )

        select 
            toYear(dt) year,
            replaceRegexpOne(ownerOrg, '^\\d+\\s*', '') category, 
            sumIf(allocated_metric, dimension like '%Payments%') capital_expenditure,
            capital_expenditure/max(inflation_adjustment.inflation_adjustment) inflation_adjusted_capital_expenditure,
            max(inflation_adjustment.inflation_adjustment)-1 cumulative_inflation_adjustment
        from summary 
        left join orgs on summary.id=orgs.cik
        left join inflation_adjustment on toYear(summary.dt)=inflation_adjustment.year
        where category!=''
        group by 
            year, 
            category
    """
    return client.query_df(query)


@cache.memoize()
def fetch_debt_free_cash_flow_by_industry():
    client = get_clickhouse_client()
    query = """
        select *
        from trading.view_free_cashflow_debt_summary
        order by insert_date desc 
        limit 1 by year,category
    """
    return client.query_df(query)

@cache.memoize()
def fetch_commitment_of_traders():
    client = get_clickhouse_client()
    query = """
    WITH base AS (
        select 
            toStartOfWeek(toDate(date)) AS dt, 
            argMax(close, dt) AS close, 
             1 AS key
        from trading.asset_prices
        where lower(ticker) ='eurusd'
        GROUP BY dt
    ), 

    cot AS (
        SELECT 
            *, 
            addDays(toStartOfWeek(report_date), 7) AS df, 
            1 AS key
        FROM (
            SELECT 
                *
            FROM trading.cot_financial_futures 
            WHERE market_and_exchange_names = 'EURO FX - CHICAGO MERCANTILE EXCHANGE'
            ORDER BY version DESC 
            LIMIT 1 BY report_date, market_and_exchange_names
        )
    )

    SELECT 
        *
    FROM base
    ASOF JOIN cot 
    ON base.key = cot.key AND base.dt >= cot.df
    """
    return client.query_df(query)

@cache.memoize()
def fetch_philippine_rice_prices():
    client = get_clickhouse_client()
    query = """
    with base as (
        select 
            toDate(insert_date) dt,
            sku,
            market,
            price,
            case 
            	when market='ever' then toFloat32OrZero(extract(sku, 's*(\\d+(\\.\\d+)?)kg')) 
            	else toFloat32OrZero(extract(sku, '\\|\\s*(\\d+(\\.\\d+)?)kg')) 
            end AS kilos
        from input_raw_products 
        where main_category='groceries'
        and (lower(sku) like '%dinurado%' or lower(sku) like '%sinandomeng%' )
        and kilos>0 
        and dt>='2025-05-24'
        order by insert_date desc 
        limit 1 by sku , dt, market
        )

        select 
            dt date, 
            avg(price/kilos) avg_price_per_kilo ,
            median(price/kilos) median_price,
            uniq(sku, market) sampled_skus
        from base
        group by dt
        order by dt
    """
    return client.query_df(query)


@cache.memoize()
def fetch_philippine_egg_prices():
    client = get_clickhouse_client()
    query = """
    with base as (
        select 
            toDate(insert_date) dt,
            sku,
            market,
            price,
            case 	
            	when market='ever' then toInt32OrZero(extract(sku, '(\\d+)')) 
            	else toInt32OrZero(extract(sku, '\\|\\s*(\\d+)'))
            end   AS pcs
        from input_raw_products 
        where 
        	main_category='groceries'
        	and lower(sku) like '%egg%'
--         	and insert_date='2025-06-22 16:52:51'
        	and lower(sku) like  '%medium%'
        	and pcs>0
        order by insert_date desc 
        limit 1 by dt, sku, market
)

      	select 
            dt date, 
            avg(price/pcs) avg_price_per_pc ,
            median(price/pcs) median_pc, 
            uniq(sku, market) sampled_skus
        from base
    group by dt
    order by dt
    """
    return client.query_df(query)



@cache.memoize()
def fetch_philippine_milk_prices():
    client = get_clickhouse_client()
    query = """
        with base as (
        SELECT
            toDate(insert_date) dt, 
            market,
            sku,
            price, 
                multiIf(
                -- Case: "X L Y pcs" or "X L Ypcs"
                match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*(\\d+)\\s*pcs'),
                    toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs')),

                -- Case: "X ml Y pcs" or "X ml Ypcs"
                match(sku, '(\\d+)\\s*[mM][lL]\\s*(\\d+)\\s*pcs'),
                    (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs'))) / 1000,

                -- Case: "X ml x Y" or "X ml x Ys"
                match(sku, '(\\d+)\\s*[mM][lL]\\s*[xX]\\s*(\\d+)s?'),
                    (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)'))) / 1000,

                -- Case: "X L x Y" or "X L x Ys"
                match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*[xX]\\s*(\\d+)s?'),
                    toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)')),

                -- Case: range in ml (e.g. "200-250ml")
                match(sku, '(\\d+)\\s*-\\s*(\\d+)\\s*[mM][lL]'),
                    ((toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 1)) +
                    toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 2))) / 2.0) / 1000,

                -- Case: "X L"
                match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]'),
                    toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')),

                -- Case: "X ml"
                match(sku, '(\\d+)\\s*[mM][lL]'),
                    toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) / 1000,

                -- Else NULL
                NULL
            ) AS volume_liters,
            case when (lower(sku) like '%almond%' or lower(sku) like '% oat %' or lower(sku) like '%soy%' or lower(sku) like '%coconut%' or lower(sku) like '%vita%') 
                then 'Alternatives' else 'Cow Milk' end category_, 
            price/volume_liters price_per_liters
            FROM default.input_raw_products
            WHERE main_category = 'groceries'
            AND lower(category) LIKE '%milk%'
            and lower(sku) not like '%evapora%'
            and lower(sku) not like '%conden%'
            and lower(sku) not like '%goat%'
            and volume_liters is not null
            and lower(sku)  not like '%whip%'
            and lower(sku) not like '%cream%'
            and lower(sku) not like '%+%'
            and lower(sku) not like '%yoghurt%'
            and  (
            		lower(sku) like '%milk%'
            		or 
            		lower(sku) like '%soy%' 
            		or 
            		lower(sku) like '%almond%' 	
            		or 
            		lower(sku) like '%oat%' 
   		
            	)
            and (lower(category) like '%fresh%' or lower(category) like '%liquid%' or category ilike '%milk%')
            order by insert_date desc
            limit 1 by dt, sku, market
            )
            select 
                dt, 
                category_ category, 
                avg(price_per_liters) mean_price,
                median(price_per_liters) median_price, 
                uniq(sku, market) sampled_skus
            from base 
            group by 
                dt, 
                category
            order by 
                dt
    """
    return client.query_df(query)


@cache.memoize()
def philippine_instant_noodles_price():
    client = get_clickhouse_client()
    query = """
        with base as (
            select
                toDate(insert_date) date, 
                sku,
                market,
                -- extract base grams
                toFloat64OrNull(extract(sku, '([0-9]+)g')) AS grams,
                
                -- extract multiplier (supports patterns like "6pcs", "x6s", "6s")
                toFloat64OrNull(
                    extract(sku, '(?:x\\s*)?([0-9]+)\\s*(?:pcs|s)')
                ) AS pcs,
                
                -- compute total grams
                (
                    toFloat64OrNull(extract(sku, '([0-9]+)g')) *
                    multiIf(
                        extract(sku, '(?:x\\s*)?([0-9]+)\\s*(?:pcs|s)') != '',
                        toFloat64OrNull(extract(sku, '(?:x\\s*)?([0-9]+)\\s*(?:pcs|s)')),
                        1
                    )
                ) AS total_grams,
                price, 
                price/total_grams pc_gram
            from default.input_raw_products
            where main_category='groceries'
            and lower(sku) like '%instant%'
            and lower(category) like '%noodle%'
            and date>'2025-05-24'
            order by insert_date desc 
            limit 1 by date, sku, market
            )
            select 
                date, 
                avg(pc_gram) * 55 mean_price, 
                median(pc_gram) * 55 median_price,
                uniq(sku, market) sampled_skus
            from base 
            group by 
                date
            order by date               
    """
    return client.query_df(query)



@cache.memoize()
def philippine_instant_3_in_1_coffee_price():
    client = get_clickhouse_client()
    query = r"""
        SELECT
            date, 
            avg(price / (weight*quantity) * 400) mean_price, 
            median(price / (weight*quantity) * 400) median_price
        FROM (
              select  
                toDate(insert_date) date,
                sku, 
                toFloat32OrZero(extract(sku, '(\\d+)\\s?g')) AS weight,
                coalesce(
                    toFloat32OrNull(
                        extract(
                            sku,
                            '\\|[^|]*?\\d+\\s?g[^0-9]*(\\d+)\\s?(?:[pP][cC][sS]?|[sS](?:achet|s)?|pack|Pack)?'
                        )
                    ),
                    1
                ) AS quantity,
                price 
            from default.input_raw_products
            where main_category='groceries'
            and (lower(category) like '%coffee%' or (category='Beverages' and market='ever'))
            and  match(sku, '\\b[0-9]+\\s?g\\b')
            and  match(sku, '\\b[Cc]offee\\b')
			and match(sku, '(?i)3[[:space:][:punct:]]*(in)?[[:space:][:punct:]]*1')
            and sku !='San Mig 3-in-1 Coffee Mix Original 20g | 30s'
            and sku not ilike '%creamer%'
            limit 1 by sku, insert_date)
            group by date
            order by date
        """
    return client.query_df(query)



@cache.memoize()
def philippine_cooking_oil():
    client = get_clickhouse_client()
    query = r"""
         SELECT
            date, 
            avg(price / adj_vol ) mean_price, 
            median(price / adj_vol) median_price, 
            uniq(sku, market) sampled_skus
        FROM (
        SELECT
            toDate(insert_date) date, 
            market,
            sku,
        coalesce(

		    -- Match 2x, 3x, "x 2", "x2", etc.
		    toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*x', 1)),
		
		    -- Match "x 2s", "x2s", "x 2pcs", "x2pcs"
		    toInt64OrNull(regexpExtract(sku, '(?i)x\\s*(\\d+)', 1)),
		
		    -- Match "2s", "2pcs", "2 pc", "2 pck"
		    toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*(s|pcs|pc|pck)', 1)),
		
		    -- Fallback
		    1
		
		) AS unit_multiplier,
            price,
            toFloat64OrNull(regexpExtract(sku, '(\\d+(?:[\\.\\/]\\d+)?)\\s*\\.?\\s*(?i)(ml|l|gallon)', 1)) AS vol,
            lower(regexpExtract(sku, '(\\d+(?:[\\.\\/]\\d+)?)\\s*\\.?\\s*(?i)(ml|l|gallon)', 2)) AS unit,
        case when unit='ml' then vol /1000 else vol end*unit_multiplier as adj_vol
        FROM default.input_raw_products
        WHERE main_category='groceries'
        AND sku ILIKE '%oil%'
        AND category ILIKE '%cooking%'
        and unit in ('ml', 'l')
        order by insert_date desc 
        limit 1 by date, sku, market )
        group by date
        """
    return client.query_df(query)


@cache.memoize()
def fetch_philippine_onion():
    client = get_clickhouse_client()
    query = r"""
        WITH
            lower(trim(substring(sku, position(sku, '|') + 1))) AS qty,
            position(qty, 'kg') > 0 AS isKg,
            toFloat64OrZero(regexpExtract(qty, '(\\d+(?:\\.\\d+)?)')) AS kg_val,
            toFloat64OrZero(regexpExtract(qty, '^(\\d+(?:\\.\\d+)?)')) AS g_left,
            toFloat64OrZero(regexpExtract(qty, '(\\d+(?:\\.\\d+)?)[^\\d]*$')) AS g_right, 
            
            base as (
        SELECT
            toDate(insert_date) date,
            sku,
            market,
            -- min_qty
            CASE
                WHEN isKg THEN 1000 * if(kg_val = 0, 1, kg_val)
                ELSE g_left
            END AS min_qty,
            -- max_qty
            CASE
                WHEN isKg THEN 1000 * if(kg_val = 0, 1, kg_val)
                ELSE g_right
            END AS max_qty, 
            case 
            	when min_qty = 0 and max_qty!=0 then max_qty
            	when min_qty != 0 and max_qty=0 then min_qty
            	else  (min_qty+max_qty)/2 
            end avg_qty,
            price , 
            price/avg_qty price_per_gram, 
            price_per_gram*375 stadard_price
        from default.input_raw_products
        where 
            main_category='groceries'
            and (sku ilike '%onion%' or sku ilike '%sibuyas%')
            and (
            		(category ilike '%fresh%' and category ilike '%vegetable%')
            		or 
            		(category ilike '%fresh%' and market='ever')
            	)
            and sku not ilike '%leeks%'
            and sku not ilike '%leave%'
            and sku not ilike '%spring%'
            and (min_qty!=0 or max_qty!=0)
            and sku not ilike '%sprout%'
        order by insert_date desc 
        limit 1 by sku, market, date
        ) 
      
        select 
            date, 
            avg(stadard_price) avg_price, 
            median(stadard_price) median_price,
            uniq(sku, market) sampled_skus
        from base 
        group by date
        order by date asc 
        """
    return client.query_df(query)



@cache.memoize()
def fetch_philippine_sugar_prices():
    client = get_clickhouse_client()
    query = r"""
        with base as (
                select 
                    toDate(insert_date) dt,
                    sku,
                    market,
                    price,
                    multiIf(
                    -- FRACTIONS like 1/2kg, 3/4 kg
                    extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg') != '',
                        (
                            toFloat64(splitByChar('/', extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg'))[1])
                            /
                            toFloat64(splitByChar('/', extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg'))[2])
                        ),
                
                    -- DECIMALS or WHOLE NUMBERS like 1kg, 1.5kg, 2.5kg
                    extract(sku, '(?i)([0-9]+(?:[.,][0-9]+)?)\\s*kg') != '',
                        toFloat64(replaceOne(
                            extract(sku, '(?i)([0-9]+(?:[.,][0-9]+)?)\\s*kg'),
                            ',',
                            '.'
                        )),
                
                    -- Default
                    NULL
                ) AS kilos, 
                price/kilos standard_price
                from default.input_raw_products 
                where 
                    main_category='groceries'
                    and sku ilike '%sugar%' 
                    and sku ilike '%refined%'   
                    and (
                        ( category ilike 'cooking%' and market='ever')
                        or 
                        ( market='sm supermarket' and category ilike '%pantry%')
                        or 
                        ( market='waltermart' and category ilike '%pantry%')
                        ) 
                    and kilos>0 
                order by insert_date desc 
                limit 1 by sku , dt, market 
        ) 
        select 
                dt date, 
                avg(standard_price) avg_price_per_kilo ,
                median(standard_price) median_price,
                uniq(sku, market) sampled_skus
        from base
        group by dt
        order by dt
        """
    return client.query_df(query)



@cache.memoize()
def philippine_instant_3_in_1_coffee_price():
    client = get_clickhouse_client()
    query = r"""
        SELECT
            date, 
            avg(price / (weight*quantity) * 400) mean_price, 
            median(price / (weight*quantity) * 400) median_price,
            uniq(sku, market) sampled_skus
        FROM (
              select  
                toDate(insert_date) date,
                market,
                sku, 
                toFloat32OrZero(extract(sku, '(\\d+)\\s?g')) AS weight,
                coalesce(
                    toFloat32OrNull(
                        extract(
                            sku,
                            '\\|[^|]*?\\d+\\s?g[^0-9]*(\\d+)\\s?(?:[pP][cC][sS]?|[sS](?:achet|s)?|pack|Pack)?'
                        )
                    ),
                    1
                ) AS quantity,
                price 
            from default.input_raw_products
            where main_category='groceries'
            and (lower(category) like '%coffee%' or (category='Beverages' and market='ever'))
            and  match(sku, '\\b[0-9]+\\s?g\\b')
            and  match(sku, '\\b[Cc]offee\\b')
			and match(sku, '(?i)3[[:space:][:punct:]]*(in)?[[:space:][:punct:]]*1')
            and sku !='San Mig 3-in-1 Coffee Mix Original 20g | 30s'
            and sku not ilike '%creamer%'
            limit 1 by sku, insert_date)
            group by date
            order by date
        """
    return client.query_df(query)



@cache.memoize()
def philippine_detergent_powder():
    client = get_clickhouse_client()
    query = r"""
        with base as (
            SELECT 
                toDate(insert_date) td, 
                sku, 
                market,

                /* ✅ extract qty from patterns like 6+1, 3+2pcs */
                case 
                    when market='ever' then toInt64OrNull(regexpExtract(sku, '(?i)(?:^|[^0-9])(\\d+)x\\s*(\\d+)\\s*(g|gr)', 1))
                else 
                    (
                        toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*\\+\\s*(\\d+)', 1)) +
                        toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*\\+\\s*(\\d+)', 2))
                    ) end AS qty_plus,

                /* ✅ extract simple multipliers: x6, 6x, 6pcs, 6s */
                coalesce(
                    toInt64OrNull(regexpExtract(sku, '(?i)\\b(\\d+)\\s*x\\b', 1)),
                    toInt64OrNull(regexpExtract(sku, '(?i)x\\s*(\\d+)', 1)),
                    toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*(pcs|s)\\b', 1)),
                    1
                ) AS qty_simple,

                /* ✅ base quantity = qty_plus fallback qty_simple */
                coalesce(qty_plus, qty_simple, 1) AS qty,

                /* ✅ base grams */
                multiIf(
                    match(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*kg'),
                        toFloat64(extract(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*kg')) * 1000.0,

                    match(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*(g|gr)'),
                        toFloat64(extract(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*(g|gr)')),

                    NULL
                ) AS grams,

                /* ✅ final total weight, rounded */
                round(grams * toFloat64(qty)) AS total_grams,

                price / total_grams AS price_per_gram

            FROM default.input_raw_products
            WHERE main_category = 'groceries'
            AND sku ILIKE '%Detergent%'
            AND sku ILIKE '%Powder%'
            and sku not ilike '%free%'
            and toDate(insert_date)>='2025-06-01'
            AND grams IS NOT NULL
            ORDER BY insert_date DESC
            limit 1 by td,  sku, market 
            )
        select 
            td date, 
            uniq(sku, market) sampled_skus,
            avg(price_per_gram * 2000) mean_price, 
            median(price_per_gram * 2000) median_price
        from base 
        group by date
        order by date
        """
    return client.query_df(query)



@cache.memoize()
def philippine_sardines():
    client = get_clickhouse_client()
    query = r"""
        with base as (
            SELECT 
                toDate(insert_date) td, 
                sku, 
                market,

                /* ✅ extract qty from patterns like 6+1, 3+2pcs */
                case 
                    when market='ever' then toInt64OrNull(regexpExtract(sku, '(?i)(?:^|[^0-9])(\\d+)x\\s*(\\d+)\\s*(g|gr)', 1))
                else 
                    (
                        toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*\\+\\s*(\\d+)', 1)) +
                        toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*\\+\\s*(\\d+)', 2))
                    ) end AS qty_plus,

                /* ✅ extract simple multipliers: x6, 6x, 6pcs, 6s */
                coalesce(
                    toInt64OrNull(regexpExtract(sku, '(?i)\\b(\\d+)\\s*x\\b', 1)),
                    toInt64OrNull(regexpExtract(sku, '(?i)x\\s*(\\d+)', 1)),
                    toInt64OrNull(regexpExtract(sku, '(?i)(\\d+)\\s*(pcs|s)\\b', 1)),
                    1
                ) AS qty_simple,

                /* ✅ base quantity = qty_plus fallback qty_simple */
                coalesce(qty_plus, qty_simple, 1) AS qty,

                /* ✅ base grams */
                multiIf(
                    match(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*kg'),
                        toFloat64(extract(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*kg')) * 1000.0,

                    match(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*(g|gr)'),
                        toFloat64(extract(sku, '(?i)(\\d+(?:\\.\\d+)?)\\s*(g|gr)')),

                    NULL
                ) AS grams,

                /* ✅ final total weight, rounded */
                round(grams * toFloat64(qty)) AS total_grams,

                price / total_grams AS price_per_gram

            FROM default.input_raw_products
            WHERE main_category = 'groceries'
    		and sku ilike '%sardin%'
    		and total_grams is not null
    		and insert_date>'2025-05-24'
            ORDER BY insert_date DESC
            limit 1 by td,  sku, market 
            )
            
   
        select 
            td date, 
            uniq(sku, market) sampled_skus,
            avg(price_per_gram * 155) mean_price, 
            median(price_per_gram * 155) median_price
        from base 
        group by date
        order by date
        """
    return client.query_df(query)


@cache.memoize()
def fetch_philippine_sugar_prices():
    client = get_clickhouse_client()
    query = r"""
        with base as (
                select 
                    toDate(insert_date) dt,
                    sku,
                    market,
                    price,
                    multiIf(
                    -- FRACTIONS like 1/2kg, 3/4 kg
                    extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg') != '',
                        (
                            toFloat64(splitByChar('/', extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg'))[1])
                            /
                            toFloat64(splitByChar('/', extract(sku, '(?i)([0-9]+/[0-9]+)\\s*kg'))[2])
                        ),
                
                    -- DECIMALS or WHOLE NUMBERS like 1kg, 1.5kg, 2.5kg
                    extract(sku, '(?i)([0-9]+(?:[.,][0-9]+)?)\\s*kg') != '',
                        toFloat64(replaceOne(
                            extract(sku, '(?i)([0-9]+(?:[.,][0-9]+)?)\\s*kg'),
                            ',',
                            '.'
                        )),
                
                    -- Default
                    NULL
                ) AS kilos, 
                price/kilos standard_price
                from default.input_raw_products 
                where 
                    main_category='groceries'
                    and sku ilike '%sugar%' 
                    and sku ilike '%refined%'   
                    and (
                        ( category ilike 'cooking%' and market='ever')
                        or 
                        ( market='sm supermarket' and category ilike '%pantry%')
                        or 
                        ( market='waltermart' and category ilike '%pantry%')
                        ) 
                    and kilos>0 
                order by insert_date desc 
                limit 1 by sku , dt, market 
        ) 
        select 
                dt date, 
                avg(standard_price) avg_price_per_kilo ,
                median(standard_price) median_price,
                uniq(sku, market) sampled_skus
        from base
        group by dt
        order by dt
        """
    return client.query_df(query)



@cache.memoize()
def philippine_white_vingar_prices():
    client = get_clickhouse_client()
    query = r"""
        with base as (
        select 	
            toDate(insert_date) date,
            sku, 
            price, 
            market, 
            multiIf(
        -- Case: "X L Y pcs" or "X L Ypcs"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*(\\d+)\\s*pcs'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs')),

        -- Case: "X ml Y pcs" or "X ml Ypcs"
        match(sku, '(\\d+)\\s*[mM][lL]\\s*(\\d+)\\s*pcs'),
            (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs'))) / 1000,

        -- Case: "X ml x Y" or "X ml x Ys"
        match(sku, '(\\d+)\\s*[mM][lL]\\s*[xX]\\s*(\\d+)s?'),
            (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)'))) / 1000,

        -- Case: "X L x Y" or "X L x Ys"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*[xX]\\s*(\\d+)s?'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)')),

        -- Case: range in ml (e.g. "200-250ml")
        match(sku, '(\\d+)\\s*-\\s*(\\d+)\\s*[mM][lL]'),
            ((toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 1)) +
            toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 2))) / 2.0) / 1000,

        -- Case: "X L"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')),

        -- Case: "X ml"
        match(sku, '(\\d+)\\s*[mM][lL]'),
            toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) / 1000,

        -- Else NULL
        NULL
                    ) AS volume_liters,
            price/volume_liters price_per_liters
        from default.input_raw_products
        where 
            main_category='groceries'
            and sku ilike '%vinegar%'
            and sku ilike '%white%'
            and volume_liters is not null
        order by insert_date desc
        limit 1 by date, sku, market
        )

        select 
            date, 
            avg(price_per_liters) mean_price,
            median(price_per_liters) median_price, 
            uniq(sku, market) sampled_skus
        from base
        group by 
            date
        order by 
            date
        """
    return client.query_df(query)



@cache.memoize()
def philippine_cane_vingar_prices():
    client = get_clickhouse_client()
    query = r"""
        with base as (
        select 	
            toDate(insert_date) date,
            sku, 
            price, 
            market, 
            multiIf(
        -- Case: "X L Y pcs" or "X L Ypcs"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*(\\d+)\\s*pcs'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs')),

        -- Case: "X ml Y pcs" or "X ml Ypcs"
        match(sku, '(\\d+)\\s*[mM][lL]\\s*(\\d+)\\s*pcs'),
            (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '(\\d+)\\s*pcs'))) / 1000,

        -- Case: "X ml x Y" or "X ml x Ys"
        match(sku, '(\\d+)\\s*[mM][lL]\\s*[xX]\\s*(\\d+)s?'),
            (toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)'))) / 1000,

        -- Case: "X L x Y" or "X L x Ys"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]\\s*[xX]\\s*(\\d+)s?'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')) * toInt32(extract(sku, '[xX]\\s*(\\d+)')),

        -- Case: range in ml (e.g. "200-250ml")
        match(sku, '(\\d+)\\s*-\\s*(\\d+)\\s*[mM][lL]'),
            ((toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 1)) +
            toFloat64(arrayElement(extractAll(sku, '(\\d+)'), 2))) / 2.0) / 1000,

        -- Case: "X L"
        match(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]'),
            toFloat64(extract(sku, '(\\d+(?:\\.\\d+)?)\\s*[lL]')),

        -- Case: "X ml"
        match(sku, '(\\d+)\\s*[mM][lL]'),
            toFloat64(extract(sku, '(\\d+)\\s*[mM][lL]')) / 1000,

        -- Else NULL
        NULL
                    ) AS volume_liters,
            price/volume_liters price_per_liters
        from default.input_raw_products
        where 
            main_category='groceries'
            and sku ilike '%vinegar%'
            and sku ilike '%cane%'
            and volume_liters is not null
        order by insert_date desc
        limit 1 by date, sku, market
        )

        select 
            date, 
            avg(price_per_liters) mean_price,
            median(price_per_liters) median_price, 
            uniq(sku, market) sampled_skus
        from base
        group by 
            date
        order by 
            date
        """
    return client.query_df(query)
