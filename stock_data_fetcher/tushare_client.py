"""
Tushare数据获取模块
"""
import tushare as ts
import time
import logging
from config import TUSHARE_TOKEN, TRADE_DAYS, REQUEST_INTERVAL

logger = logging.getLogger(__name__)


class TushareClient:
    def __init__(self):
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        logger.info("Tushare客户端初始化成功")

    def get_stock_list(self):
        """获取股票列表(DataFrame格式)"""
        try:
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            logger.info(f"获取到 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return None

    def get_stock_info_list(self):
        """获取股票信息(字典列表格式，便于保存到数据库)"""
        try:
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            
            if df is not None and not df.empty:
                stock_list = []
                for _, row in df.iterrows():
                    stock_list.append({
                        'ts_code': row.get('ts_code'),
                        'symbol': row.get('symbol'),
                        'name': row.get('name'),
                        'area': row.get('area'),
                        'industry': row.get('industry'),
                        'list_date': row.get('list_date')
                    })
                logger.info(f"获取到 {len(stock_list)} 只股票信息")
                return stock_list
            return []
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return []

    def get_trade_dates(self, days=TRADE_DAYS):
        """获取最近N个交易日期"""
        try:
            import datetime
            end_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days*2)).strftime('%Y%m%d')
            
            df = self.pro.trade_cal(
                exchange='SSE',
                start_date=start_date,
                end_date=end_date,
                is_open='1'
            )
            
            trade_dates = df[df['is_open']==1]['cal_date'].tolist()
            trade_dates.sort()
            
            recent_dates = trade_dates[-days:] if len(trade_dates) >= days else trade_dates
            
            if recent_dates:
                return recent_dates[0], recent_dates[-1]
            return None, None
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return None, None

    def get_daily_data(self, ts_code, start_date, end_date):
        """获取单只股票的日线数据"""
        try:
            time.sleep(REQUEST_INTERVAL)
            
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                data_list = []
                for _, row in df.iterrows():
                    data_list.append({
                        'ts_code': row.get('ts_code'),
                        'trade_date': row.get('trade_date'),
                        'open': row.get('open'),
                        'high': row.get('high'),
                        'low': row.get('low'),
                        'close': row.get('close'),
                        'pre_close': row.get('pre_close'),
                        'change': row.get('change'),
                        'pct_chg': row.get('pct_chg'),
                        'vol': row.get('vol'),
                        'amount': row.get('amount')
                    })
                return data_list
            return []
        except Exception as e:
            logger.error(f"获取 {ts_code} 日线数据失败: {e}")
            return []
