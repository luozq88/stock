import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM stock_info')
stock_count = cursor.fetchone()[0]
print(f'股票信息表 (stock_info): {stock_count} 条记录')

cursor.execute('SELECT COUNT(*) FROM daily_data')
daily_count = cursor.fetchone()[0]
print(f'日线数据表 (daily_data): {daily_count} 条记录')

cursor.execute('SELECT COUNT(DISTINCT ts_code) FROM daily_data')
stock_with_daily = cursor.fetchone()[0]
print(f'已有日线数据的股票数: {stock_with_daily} 只')

cursor.execute('SELECT MIN(trade_date), MAX(trade_date) FROM daily_data')
date_range = cursor.fetchone()
if date_range[0]:
    print(f'数据日期范围: {date_range[0]} 至 {date_range[1]}')

cursor.execute('SELECT ts_code, COUNT(*) as cnt FROM daily_data GROUP BY ts_code ORDER BY cnt DESC LIMIT 5')
top_stocks = cursor.fetchall()
print(f'\n数据量最多的5只股票:')
for stock in top_stocks:
    print(f'  {stock[0]}: {stock[1]} 条记录')

conn.close()
