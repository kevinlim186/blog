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
    with base as (
        SELECT 
            entity,
            date,
            case  
            	when t.dimension  like '%Provided%' or dimension like '%Payments%' then 'Free Cashflow'
            	when t.dimension like '%Debt%'  then 'Long Term Debt'
            end dimension,
            id,
            case
            	when  t.dimension  like '%Provided%'  then metric / (dateDiff('day', start, end) + 1) 
            	when  t.dimension  like '%Payments%'  then -metric / (dateDiff('day', start, end) + 1) 
            	else metric
            end AS allocated_metric
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
		                        ((dimension LIKE '%Net Cash Provided by (Used in) Operating Activities, Continuing Operations%'
		                        or 
		                        dimension like  'Net Cash Provided by (Used in) Operating Activities'
		                        or
		                        dimension= 'Payments to Acquire Property, Plant, and Equipment'
		                        or 
		                        dimension like 'Payments to Acquire Intangible Assets'
		                        )
		                        and    dateDiff('day', start, end) > 350
                    			)
                    			
								or 
									(LOWER(dimension) IN (
									    'long-term debt, gross',
									    'long-term debt, current maturities',
									    'short-term debt'
									  )  and start='1970-01-01')
									                     
                    )	
--                    and entity like '%Apple Inc.%'
                    AND id !='707605' -- faulty data
                    AND end >= '2009-01-01'
                    AND form = '10-K'
                ORDER BY created_at DESC, filed DESC 
                LIMIT 1 BY start, end, entity, dimension
            ) AS input
            ARRAY JOIN range(CAST(dateDiff('day', start, end) + 1 AS UInt64)) AS number
        
        ) t
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
            case 
            	when dimension='Free Cashflow' then sum(allocated_metric) 
            	else max(allocated_metric) 
            end allocated_metric
        from base
        group by dt, dimension, id
        )

        select 
            toYear(dt) year,
            replaceRegexpOne(ownerOrg, '^\\d+\\s*', '') category, 
            sumIf(allocated_metric, dimension like '%Long Term Debt%')/uniq(id) avg_long_term_debt,
            sumIf(allocated_metric, dimension like '%Free Cashflow%')/uniq(id)  avg_free_cash_flow, 
            avg_free_cash_flow/avg_long_term_debt  free_cash_flow_to_long_term_debt
        from summary 
        left join orgs on summary.id=orgs.cik
        where category!=''
        group by 
            year, 
            category
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
            toFloat32OrZero(extract(sku, '\\|\\s*(\\d+(\\.\\d+)?)kg')) AS kilos
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
            median(price/kilos) median_price
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
            toInt32OrZero(extract(sku, '\\|\\s*(\\d+)')) AS pcs
        from input_raw_products 
        where 
        	main_category='groceries'
        	and lower(sku) like '%egg%'
--         	and insert_date='2025-06-22 16:52:51'
        	and lower(sku) like  '%medium%'
        	and pcs>0
)

      	select 
            dt date, 
            avg(price/pcs) avg_price_per_pc ,
            median(price/pcs) median_pc
        from base
    group by dt
    order by dt
    """
    return client.query_df(query)
