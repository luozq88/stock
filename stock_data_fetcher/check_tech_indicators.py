import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM tech_indicators')
tech_count = cursor.fetchone()[0]
print(f'技术指标表 (tech_indicators): {tech_count} 条记录')

cursor.execute('SELECT COUNT(DISTINCT ts_code) FROM tech_indicators')
stock_with_tech = cursor.fetchone()[0]
print(f'已有技术指标的股票数: {stock_with_tech} 只')

cursor.execute('''
    SELECT ti.ts_code, si.name, ti.trade_date, ti.ma5, ti.ma10, ti.ma20, ti.vol5 
    FROM tech_indicators ti 
    LEFT JOIN stock_info si ON ti.ts_code = si.ts_code 
    ORDER BY ti.trade_date DESC, ti.ts_code 
    LIMIT 10
''')
rows = cursor.fetchall()
print(f'\n最新技术指标样本:')
print(f'{"ts_code":<12} {"name":<10} {"trade_date":<10} {"ma5":<8} {"ma10":<8} {"ma20":<8} {"vol5":<12}')
print('-' * 70)
for row in rows:
    print(f'{row[0]:<12} {str(row[1]):<10} {str(row[2]):<10} {str(row[3]):<8} {str(row[4]):<8} {str(row[5]):<8} {str(row[6]):<12}')

conn.close()
