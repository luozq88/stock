import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM stock_info')
print(f'Total stock info records: {cursor.fetchone()[0]}')

cursor.execute('SELECT * FROM stock_info LIMIT 10')
rows = cursor.fetchall()
print(f'\nSample stock info:')
print(f'{"ts_code":<12} {"symbol":<10} {"name":<10} {"area":<8} {"industry":<15} {"list_date":<10}')
print('-' * 70)
for row in rows:
    print(f'{row[0]:<12} {row[1]:<10} {row[2]:<10} {str(row[3]):<8} {str(row[4]):<15} {str(row[5]):<10}')

conn.close()
