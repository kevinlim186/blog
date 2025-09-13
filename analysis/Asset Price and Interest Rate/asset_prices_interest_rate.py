from data.db_client import get_clickhouse_client
import pandas as pd
import numpy as np
from sklearn.metrics import mutual_info_score, log_loss
import scipy.stats as ss
import yfinance as yf

from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from tqdm import tqdm
import numpy as np
import pandas as pd



sql ='''
WITH 

prices AS (
    SELECT
        cik,
        argMax(ticker,version) ticker
    FROM trading.asset_prices 
    where cik !='' and date>='2010-01-01'
    group by 
    	cik
)

SELECT 
	ticker, cik, "sicDescription", "ownerOrg",name
FROM prices
inner join trading.equity_companies on trading.equity_companies.cik =prices.cik
order by created_at desc
limit 1 by ticker
'''

interest_sql = '''
select *
from trading.economic_calendar
where attribute like '%_interest'
and date>='2010-01-01'
order by version desc 
limit 1 by date, attribute
'''


def numBins(nObs,corr=None):
# Optimal number of bins for discretization 
    if corr is None: # univariate case
        z=(8+324*nObs+12*(36*nObs+729*nObs**2)**.5)**(1/3.)
        b=round(z/6.+2./(3*z)+1./3) 
    else: # bivariate case
        if (1.-corr**2)==0:
            corr = np.sign(corr)*(np.abs(corr)-1e-5)  
        b=2**-.5*(1+(1+24*nObs/(1.-corr**2))**.5)**.5

        if not np.isfinite(b):
            return 2
        return min(max(2, int(round(b))), 2056)

def varInfo_optBIn(x,y,norm=False): # Discretized and with optimal bin value
    # variation of information
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) == 0 or len(y) == 0:
        return 1
    corr = np.corrcoef(x, y)[0, 1]
    bXY = numBins(x.shape[0], corr=corr)

    cXY = np.histogram2d(x, y, bXY)[0]
    iXY = mutual_info_score(None, None, contingency=cXY)
    hX = ss.entropy(np.histogram(x, bXY)[0])  # marginal
    hY = ss.entropy(np.histogram(y, bXY)[0])  # marginal
    vXY = hX + hY - 2 * iXY  # variation of information
    if norm:
        hXY = hX + hY - iXY  # joint
        vXY /= hXY  # normalized variation of information
    return vXY

def compute_vi(df, col1, col2):
    df_temp = df[[col1, col2]].dropna()
    x = df_temp[col1].values
    y = df_temp[col2].values
    vXY = varInfo_optBIn(x=x, y=y, norm=True)
    return col1, col2, vXY


client = get_clickhouse_client()
data = client.query_df(sql)
interest = client.query_df(interest_sql)



tickers= list(data.ticker.unique())
start='2010-01-01'
prices_list = []

def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

for batch in _chunks(tickers, 200):  # download in batches to avoid spawning thousands of threads
    p = yf.download(batch, start=start, auto_adjust=True, progress=True, threads=8)["Close"]
    # Normalize each batch index (tz-naive, unique, sorted)
    p.index = pd.to_datetime(p.index)
    if getattr(p.index, "tz", None) is not None:
        p.index = p.index.tz_localize(None)
    p = p[~p.index.duplicated(keep="last")]
    p = p.sort_index()
    prices_list.append(p)
# Concatenate all batches side-by-side
prices = pd.concat(prices_list, axis=1)
prices = prices.dropna(axis=1, how="all")

prices.index = pd.to_datetime(prices.index)
if getattr(prices.index, "tz", None) is not None:
    prices.index = prices.index.tz_localize(None)

# Ensure the price index is unique and sorted (yfinance can occasionally return duplicate dates)
prices = prices[~prices.index.duplicated(keep="last")]
prices = prices.sort_index()

# Shares (build a DataFrame aligned to the same index)
shares_df = pd.DataFrame(index=prices.index, columns=tickers, dtype="float64")

tickers = list(prices.columns)
for t in tickers:
    print(f'Getting {t}')
    tmp = pd.DataFrame(shares_df[t]).dropna()

    if len(tmp)>0:
        print(f'Ignoring {t}')
    else:
        tk = yf.Ticker(t)
        sh = tk.get_shares_full(start=start)

        # Normalize `sh` to a Series of shares indexed by DatetimeIndex
        if sh is None or (hasattr(sh, "empty") and sh.empty):
            sh_val = (
                tk.fast_info.get("shares")
                or tk.fast_info.get("shares_outstanding")
                or (tk.info.get("sharesOutstanding") if hasattr(tk, "info") else None)
            )
            if sh_val is None:
                # If still None, default to NaN series (will be handled below)
                sh = pd.Series(index=pd.Index([prices.index.min()], name="Date"), dtype="float64")
            else:
                sh = pd.Series(sh_val, index=pd.Index([prices.index.min()], name="Date"))
        else:
            # Convert DataFrame -> Series if needed by picking the most relevant column
            if isinstance(sh, pd.DataFrame):
                # Prefer a column that mentions 'share' in its name; otherwise take the first column
                cols = [c for c in sh.columns if "share" in str(c).lower()]
                col = cols[0] if cols else sh.columns[0]
                sh = sh[col]
            # Ensure datetime index
            sh.index = pd.to_datetime(sh.index)
            if getattr(sh.index, "tz", None) is not None:
                sh.index = sh.index.tz_localize(None)

        sh = sh[~sh.index.duplicated(keep="last")]
        sh_aligned = sh.reindex(prices.index, method="ffill").astype("float64")
        if sh_aligned.isna().all():
            sh_val = (
                tk.fast_info.get("shares")
                or tk.fast_info.get("shares_outstanding")
                or (tk.info.get("sharesOutstanding") if hasattr(tk, "info") else None)
            )
            if sh_val is not None:
                sh_aligned = pd.Series(float(sh_val), index=prices.index, dtype="float64")
        shares_df[t] = sh_aligned

market_caps = prices * shares_df

prices.to_csv('prices.csv')
shares_df.to_csv('shares_df.csv')


mc_long = market_caps.reset_index().melt(
    id_vars="Date",  # or "date" depending on your index name
    var_name="ticker",
    value_name="market_cap"
)



data = data.merge(mc_long, on='ticker', how='inner' )

interest = interest.pivot_table(columns=['attribute'], index=['date'], values=['value']).reset_index()
interest.columns = interest.columns.get_level_values(-1)
interest.rename(columns={'':'date'}, inplace=True)

data.rename(columns={'Date':'date'}, inplace=True)

group_data = data.pivot_table(columns='ownerOrg', index='date', values='market_cap', aggfunc='mean').reset_index()
sub_group_data = data.pivot_table(columns='sicDescription', index='date', values='market_cap', aggfunc='mean').reset_index()
company_data  = data.pivot_table(columns='ticker', index='date', values='market_cap', aggfunc='mean').reset_index()


group_correl =[]
sub_group_correl = []
company_correl = []

for interest_col in interest.columns[1:]:
    for grp_col in group_data.columns[2:]:
        int_df = interest[['date', interest_col]]
        grp_df = group_data[['date', grp_col]]
        merged_df = grp_df.merge(int_df, on='date')
        merged_df = merged_df.dropna()
        corr = merged_df[[interest_col, grp_col]].corr()
        vi = compute_vi(merged_df, interest_col, grp_col)
        group_correl.append({'int': interest_col, 'grp': grp_col, 'corr':  corr.iloc[0][grp_col], 'vi': vi[-1]})

group_correl = pd.DataFrame(group_correl)


for interest_col in interest.columns[1:]:
    for sub_grp_col in sub_group_data.columns[2:]:
        int_df = interest[['date', interest_col]]
        sub_grp_df = sub_group_data[['date', sub_grp_col]]
        merged_df = sub_grp_df.merge(int_df, on='date')
        merged_df = merged_df.dropna()
        corr = merged_df[[interest_col, sub_grp_col]].corr()
        vi = compute_vi(merged_df, interest_col, sub_grp_col)
        sub_group_correl.append({'int': interest_col, 'grp': sub_grp_col, 'corr':  corr.iloc[0][sub_grp_col], 'vi': vi[-1]})

sub_group_correl = pd.DataFrame(sub_group_correl)



# interest, company_data, compute_vi already defined
interest_cols = list(interest.columns[1:])
company_cols  = list(company_data.columns[1:])  # date is col 0

def _pair_job(interest_col, company_col):
    int_df  = interest[['date', interest_col]]
    comp_df = company_data[['date', company_col]]
    merged  = comp_df.merge(int_df, on='date', how='inner').dropna()
    if merged.empty:
        return None
    corr = float(np.corrcoef(merged[interest_col].values,
                             merged[company_col].values)[0, 1])
    vi   = compute_vi(merged, interest_col, company_col)
    return {'int': interest_col, 'grp': company_col, 'corr': corr, 'vi': vi[-1]}

tasks = list(product(interest_cols, company_cols))
results = []
with ThreadPoolExecutor() as ex:
    futures = [ex.submit(_pair_job, i, c) for i, c in tasks]
    for f in tqdm(as_completed(futures), total=len(futures), desc="Processing pairs"):
        r = f.result()
        if r is not None:
            results.append(r)

company_correl = pd.DataFrame(results)


names = data[['ticker','name']].drop_duplicates()
latest_mc = (
    data.dropna(subset=["market_cap"])              # drop rows with NaN market cap
        .sort_values(["ticker", "date"])            # sort by ticker + date
        .groupby("ticker")                          # group by ticker
        .tail(1)[["ticker", "market_cap", "date"]]  # take the last row
        .reset_index(drop=True)
)


company_correl = company_correl.merge(names, left_on='grp', right_on='ticker')
company_correl = company_correl.merge(latest_mc, left_on='grp', right_on='ticker')

group_correl.to_csv('group.csv')
sub_group_correl.to_csv('sub_group.csv')
company_correl.to_csv('test.csv')