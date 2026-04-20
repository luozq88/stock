"""
选股策略模块
"""
import os
import datetime
import tushare as ts
import pandas as pd
import logging
import requests
from config import TUSHARE_TOKEN
from database import Database

logger = logging.getLogger(__name__)


class StockStrategy:
    def __init__(self):
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        self.db = Database()
        logger.info("选股策略模块初始化成功")

    def get_realtime_quotes(self):
        try:
            df = ts.realtime_quote(ts_code='')
            if df is not None and not df.empty:
                logger.info(f"获取到 {len(df)} 只股票的实时行情")
                return df
            return None
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None

    def get_realtime_from_sina(self):
        try:
            import re
            stock_codes = []

            cursor = self.db.conn.cursor()
            cursor.execute('SELECT ts_code FROM stock_info')
            rows = cursor.fetchall()
            stock_codes = [row['ts_code'] for row in rows]

            all_data = []
            batch_size = 100

            for i in range(0, len(stock_codes), batch_size):
                batch = stock_codes[i:i+batch_size]
                qt_codes = []
                for code in batch:
                    if code.endswith('.SH'):
                        qt_codes.append(f"sh{code[:-3]}")
                    else:
                        qt_codes.append(f"sz{code[:-3]}")

                qt_url = f"http://qt.gtimg.cn/q={','.join(qt_codes)}"
                resp = requests.get(qt_url, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split(';')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        match = re.search(r'v_(\w+)="(.+)"', line)
                        if match:
                            code = match.group(1)
                            fields = match.group(2).split('~')
                            if len(fields) > 40:
                                stock_code = code[2:]
                                exchange = 'SH' if code.startswith('sh') else 'SZ'
                                ts_code = f"{stock_code}.{exchange}"
                                all_data.append({
                                    'ts_code': ts_code,
                                    'close': float(fields[3]) if fields[3] else 0,
                                    'pct_chg': float(fields[32]) if fields[32] else 0,
                                    'vol': float(fields[6]) if fields[6] else 0
                                })

            if all_data:
                df = pd.DataFrame(all_data)
                logger.info(f"从腾讯财经获取到 {len(df)} 只股票实时行情")
                return df
            return None
        except Exception as e:
            logger.error(f"从新浪财经获取数据失败: {e}")
            return None

    def get_realtime_from_tencent(self):
        try:
            url = 'http://qt.gtimg.cn/q=sh000001,sz399001'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                import re
                text = response.text
                stock_codes = []
                
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT ts_code FROM stock_info')
                rows = cursor.fetchall()
                stock_codes = [row['ts_code'] for row in rows]
                
                batch_size = 100
                all_data = []
                
                for i in range(0, len(stock_codes), batch_size):
                    batch = stock_codes[i:i+batch_size]
                    qt_codes = []
                    for code in batch:
                        if code.endswith('.SH'):
                            qt_codes.append(f"sh{code[:-3]}")
                        else:
                            qt_codes.append(f"sz{code[:-3]}")
                    
                    qt_url = f"http://qt.gtimg.cn/q={','.join(qt_codes)}"
                    resp = requests.get(qt_url, timeout=10)
                    if resp.status_code == 200:
                        lines = resp.text.strip().split(';')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            match = re.search(r'v_(\w+)="(.+)"', line)
                            if match:
                                code = match.group(1)
                                fields = match.group(2).split('~')
                                if len(fields) > 40:
                                    all_data.append({
                                        'ts_code': f"{fields[2].lower()}{fields[3]}",
                                        'close': float(fields[3]) if fields[3] else 0,
                                        'pct_chg': float(fields[32]) if fields[32] else 0,
                                        'vol': float(fields[6]) if fields[6] else 0
                                    })
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    logger.info(f"从腾讯财经获取到 {len(df)} 只股票实时行情")
                    return df
            return None
        except Exception as e:
            logger.error(f"从腾讯财经获取数据失败: {e}")
            return None

    def get_realtime_from_tushare(self):
        try:
            df = ts.realtime_quote(ts_code='')
            if df is not None and not df.empty:
                logger.info(f"从Tushare获取到 {len(df)} 只股票实时行情")
                return df
            return None
        except Exception as e:
            logger.error(f"从Tushare获取实时行情失败: {e}")
            return None

    def screen_stocks(self):
        logger.info("=" * 50)
        logger.info("开始执行选股策略...")
        logger.info("=" * 50)

        prev_date = self.db.get_latest_trade_date()
        if not prev_date:
            logger.error("数据库中无历史数据")
            return []

        logger.info(f"前一交易日（数据库最新）: {prev_date}")

        prev_tech = self.db.get_tech_indicators(prev_date)
        if not prev_tech:
            logger.error("前一交易日无技术指标数据")
            return []

        tech_dict = {}
        for row in prev_tech:
            tech_dict[row['ts_code']] = {
                'ma5': row['ma5'],
                'ma10': row['ma10'],
                'ma20': row['ma20'],
                'vol5': row['vol5']
            }

        logger.info(f"获取到 {len(tech_dict)} 只股票的前一日技术指标")

        realtime_df = self.get_realtime_from_sina()
        if realtime_df is None or realtime_df.empty:
            logger.warning("新浪财经数据获取失败，尝试腾讯财经...")
            realtime_df = self.get_realtime_from_tencent()

        if realtime_df is None or realtime_df.empty:
            logger.warning("腾讯财经数据获取失败，尝试Tushare...")
            realtime_df = self.get_realtime_from_tushare()

        if realtime_df is None or realtime_df.empty:
            logger.error("所有实时行情数据源均获取失败")
            return []

        logger.info(f"获取到 {len(realtime_df)} 只股票的当日实时数据")

        selected_stocks = []

        for _, row in realtime_df.iterrows():
            ts_code = row['ts_code']

            if ts_code not in tech_dict:
                continue

            tech = tech_dict[ts_code]

            pct_chg = row.get('pct_chg')
            if pct_chg is None or pd.isna(pct_chg):
                continue

            if pct_chg < 1.5 or pct_chg > 8.0:
                continue

            current_price = row.get('close')
            if current_price is None or pd.isna(current_price) or current_price <= 0:
                continue

            if current_price <= tech['ma5']:
                continue
            if current_price <= tech['ma10']:
                continue
            if current_price <= tech['ma20']:
                continue

            today_vol = row.get('vol')
            if today_vol is None or pd.isna(today_vol) or today_vol <= 0:
                continue

            current_hour = datetime.datetime.now().hour
            current_minute = datetime.datetime.now().minute

            if 11 <= current_hour <= 12:
                vol_ratio_threshold = 0.9
            elif current_hour == 14 and current_minute <= 30:
                vol_ratio_threshold = 1.3
            elif current_hour == 10 and current_minute >= 30:
                vol_ratio_threshold = 0.8
            else:
                vol_ratio_threshold = 1.0

            vol_threshold = tech['vol5'] * vol_ratio_threshold
            if today_vol < vol_threshold:
                continue

            selected_stocks.append({
                'ts_code': ts_code,
                'current_price': current_price,
                'pct_chg': pct_chg,
                'today_vol': today_vol,
                'prev_ma5': tech['ma5'],
                'prev_ma10': tech['ma10'],
                'prev_ma20': tech['ma20'],
                'prev_vol5': tech['vol5'],
                'vol_ratio': today_vol / vol_threshold if vol_threshold > 0 else 0
            })

        selected_stocks.sort(key=lambda x: x['pct_chg'], reverse=True)

        if selected_stocks:
            ts_codes = [s['ts_code'] for s in selected_stocks]
            stock_info_list = self.db.get_stock_info_by_codes(ts_codes)
            info_dict = {}
            for info in stock_info_list:
                info_dict[info['ts_code']] = {
                    'name': info['name'],
                    'industry': info['industry']
                }

            for stock in selected_stocks:
                if stock['ts_code'] in info_dict:
                    stock['name'] = info_dict[stock['ts_code']]['name']
                    stock['industry'] = info_dict[stock['ts_code']]['industry']
                else:
                    stock['name'] = '未知'
                    stock['industry'] = '未知'

        logger.info(f"筛选完成，共选出 {len(selected_stocks)} 只股票")
        return selected_stocks

    def save_to_file(self, selected_stocks, filename="selected_stocks.txt"):
        if not selected_stocks:
            logger.info("未筛选到符合条件的股票")
            return

        output_dir = os.path.dirname(os.path.dirname(__file__))
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            for stock in selected_stocks:
                f.write(f"{stock['ts_code']}\n")

        logger.info(f"选股结果已保存到: {filepath}")

    def print_results(self, selected_stocks):
        if not selected_stocks:
            logger.info("未筛选到符合条件的股票")
            return

        self.save_to_file(selected_stocks)

        print("\n" + "=" * 120)
        print(f"{'代码':<12} {'名称':<10} {'涨幅%':<8} {'现价':<8} {'MA5':<8} {'MA10':<8} {'MA20':<8} {'今日量':<12} {'VOL5':<12} {'量比':<8} {'行业':<15}")
        print("-" * 120)

        for stock in selected_stocks:
            print(f"{stock['ts_code']:<12} "
                  f"{stock['name']:<10} "
                  f"{stock['pct_chg']:<8.2f} "
                  f"{stock['current_price']:<8.2f} "
                  f"{stock['prev_ma5']:<8.2f} "
                  f"{stock['prev_ma10']:<8.2f} "
                  f"{stock['prev_ma20']:<8.2f} "
                  f"{stock['today_vol']:<12.0f} "
                  f"{stock['prev_vol5']:<12.0f} "
                  f"{stock['vol_ratio']:<8.2f} "
                  f"{stock['industry']:<15}")

        print("=" * 120)
        print(f"共选出 {len(selected_stocks)} 只股票")
        print("=" * 120)

    def close(self):
        self.db.close()
