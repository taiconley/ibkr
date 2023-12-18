import sys
sys.path.append("/ibkr")

tickdata_date = 'tickdata_aug1'

sql_last_tick = f"""
SELECT timestamp FROM {tickdata_date}_l2 ORDER BY timestamp DESC LIMIT 1
"""

sql_total_ticks = f"""
SELECT COUNT(*) FROM {tickdata_date}_l2
"""

sql_buying_power = '''
    SELECT 
    val
    FROM public.account_summary
    where "key" = 'BuyingPower'
    order by "timestamp" desc
    limit 1
'''

sql_total_ES_positions = '''
    SELECT 
    pos
    FROM public.positions
    where "symbol" = 'ES'
    order by "timestamp" desc
    limit 1
'''

sql_current_live_price = '''
    SELECT current_price
    from public.predictions
    order by "timestamp" desc
    limit 1
'''

sql_current_predicted_price = '''
    SELECT predicted_price
    from public.predictions
    order by "timestamp" desc
    limit 1
'''

sql_gross_position_value = '''
    SELECT 
    val
    FROM public.account_summary
    where "key" = 'GrossPositionValue-S'
    order by "timestamp" desc
    limit 1
'''

sql_unrealized_pnl = '''
    SELECT 
    val
    FROM public.account_summary
    where "key" = 'UnrealizedPnL'
    order by "timestamp" desc
    limit 1
'''

sql_realized_pnl = '''
    SELECT 
    val
    FROM public.account_summary
    where "key" = 'RealizedPnL'
    order by "timestamp" desc
    limit 1
'''

sql_cash_balance = '''
    SELECT 
    val
    FROM public.account_summary
    where "key" = 'CashBalance'
    order by "timestamp" desc
    limit 1
'''

sql_l2 = f'''
SELECT *
FROM {tickdata_date}_l2;
'''

###### Queries for pairs

sql_pairs_tickers = f'''
SELECT * FROM public.pairs_ticker_list
'''