import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM daily_data')
print(f'Total records: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(DISTINCT ts_code) FROM daily_data')
print(f'Total stocks: {cursor.fetchone()[0]}')

cursor.execute('SELECT * FROM daily_data LIMIT 5')
rows = cursor.fetchall()
print(f'\nSample data:')
for row in rows:
    print(row)

conn.close()
