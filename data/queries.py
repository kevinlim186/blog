from .db_client import get_clickhouse_client

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
                interpolated_german_breakeven_inflation*100 interpolated_german_breakeven_inflation, us_10_year_breakeven_inflation_rate us_breakeven_inflation,  us_ten_year_interest-us_10_year_breakeven_inflation_rate us_implied_tips, 
                eur_usd_fx,     
                interpolated_yield_bond*100 interpolated_yield_bond, 
                interpolated_yield_tips*100 interpolated_yield_tips, 
                us_ten_year_interest
            from german_bonds
            inner join us_inflation on (us_inflation.date=german_bonds.date)
            inner join eur_usd on (eur_usd.date=german_bonds.date)
            where date>='2010-01-01'
    """
    return client.query_df(query)