"""
数据库操作模块
"""
import sqlite3
import os
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        logger.info(f"数据库连接成功: {self.db_path}")

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                ts_code TEXT PRIMARY KEY,
                symbol TEXT,
                name TEXT,
                area TEXT,
                industry TEXT,
                list_date TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT,
                trade_date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                pre_close REAL,
                change REAL,
                pct_chg REAL,
                vol REAL,
                amount REAL,
                UNIQUE(ts_code, trade_date)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_ts_code ON daily_data(ts_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_trade_date ON daily_data(trade_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_code_date ON daily_data(ts_code, trade_date)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tech_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT,
                trade_date TEXT,
                ma5 REAL,
                ma10 REAL,
                ma20 REAL,
                vol5 REAL,
                calculated_at TEXT,
                UNIQUE(ts_code, trade_date)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_ts_code ON tech_indicators(ts_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_trade_date ON tech_indicators(trade_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_code_date ON tech_indicators(ts_code, trade_date)')
        
        self.conn.commit()
        logger.info("数据表创建完成")

    def insert_stock_info(self, data_list):
        if not data_list:
            return 0
        
        cursor = self.conn.cursor()
        inserted = 0
        
        import datetime
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for data in data_list:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_info 
                    (ts_code, symbol, name, area, industry, list_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('ts_code'),
                    data.get('symbol'),
                    data.get('name'),
                    data.get('area'),
                    data.get('industry'),
                    data.get('list_date'),
                    current_time
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"插入股票信息失败: {e}")
        
        self.conn.commit()
        logger.info(f"成功插入 {inserted} 条股票信息")
        return inserted

    def insert_daily_data(self, data_list):
        if not data_list:
            return 0
        
        cursor = self.conn.cursor()
        inserted = 0
        
        for data in data_list:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_data 
                    (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('ts_code'),
                    data.get('trade_date'),
                    data.get('open'),
                    data.get('high'),
                    data.get('low'),
                    data.get('close'),
                    data.get('pre_close'),
                    data.get('change'),
                    data.get('pct_chg'),
                    data.get('vol'),
                    data.get('amount')
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"插入数据失败: {e}")
        
        self.conn.commit()
        logger.info(f"成功插入 {inserted} 条日线数据")
        return inserted

    def get_latest_date(self, ts_code):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MAX(trade_date) as max_date FROM daily_data WHERE ts_code = ?
        ''', (ts_code,))
        result = cursor.fetchone()
        return result['max_date'] if result else None

    def insert_tech_indicators(self, data_list):
        if not data_list:
            return 0
        
        cursor = self.conn.cursor()
        inserted = 0
        
        import datetime
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for data in data_list:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO tech_indicators 
                    (ts_code, trade_date, ma5, ma10, ma20, vol5, calculated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('ts_code'),
                    data.get('trade_date'),
                    data.get('ma5'),
                    data.get('ma10'),
                    data.get('ma20'),
                    data.get('vol5'),
                    current_time
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"插入技术指标失败: {e}")
        
        self.conn.commit()
        logger.info(f"成功插入 {inserted} 条技术指标数据")
        return inserted

    def get_latest_trade_date(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(trade_date) FROM daily_data')
        result = cursor.fetchone()
        return result[0] if result else None

    def get_previous_trade_date(self, trade_date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MAX(trade_date) FROM daily_data WHERE trade_date < ?
        ''', (trade_date,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_tech_indicators(self, trade_date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ts_code, trade_date, ma5, ma10, ma20, vol5
            FROM tech_indicators
            WHERE trade_date = ?
            AND ma5 IS NOT NULL AND ma10 IS NOT NULL AND ma20 IS NOT NULL AND vol5 IS NOT NULL
        ''', (trade_date,))
        return cursor.fetchall()

    def get_stock_info_by_codes(self, ts_codes):
        if not ts_codes:
            return []
        cursor = self.conn.cursor()
        placeholders = ','.join(['?' for _ in ts_codes])
        cursor.execute(f'''
            SELECT ts_code, symbol, name, area, industry
            FROM stock_info
            WHERE ts_code IN ({placeholders})
        ''', ts_codes)
        return cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")
