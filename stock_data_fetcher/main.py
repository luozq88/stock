"""
主程序入口 - 获取日线数据并保存到SQLite
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import LOG_LEVEL, LOG_FORMAT, TRADE_DAYS
from database import Database
from tushare_client import TushareClient


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )


def calculate_tech_indicators(daily_data):
    if not daily_data or len(daily_data) < 20:
        return []
    
    sorted_data = sorted(daily_data, key=lambda x: x['trade_date'])
    
    tech_list = []
    
    for i in range(len(sorted_data)):
        if i < 4:
            continue
        
        close_prices = [sorted_data[j]['close'] for j in range(max(0, i-4), i+1) if sorted_data[j]['close'] is not None]
        
        ma5 = sum(close_prices[-5:]) / 5 if len(close_prices) >= 5 else None
        
        close_prices_10 = [sorted_data[j]['close'] for j in range(max(0, i-9), i+1) if sorted_data[j]['close'] is not None]
        ma10 = sum(close_prices_10) / len(close_prices_10) if len(close_prices_10) >= 10 else None
        
        close_prices_20 = [sorted_data[j]['close'] for j in range(max(0, i-19), i+1) if sorted_data[j]['close'] is not None]
        ma20 = sum(close_prices_20) / len(close_prices_20) if len(close_prices_20) >= 20 else None
        
        vol_prices = [sorted_data[j]['vol'] for j in range(max(0, i-4), i+1) if sorted_data[j]['vol'] is not None]
        vol5 = sum(vol_prices) / len(vol_prices) if len(vol_prices) >= 5 else None
        
        tech_list.append({
            'ts_code': sorted_data[i]['ts_code'],
            'trade_date': sorted_data[i]['trade_date'],
            'ma5': round(ma5, 4) if ma5 else None,
            'ma10': round(ma10, 4) if ma10 else None,
            'ma20': round(ma20, 4) if ma20 else None,
            'vol5': round(vol5, 4) if vol5 else None
        })
    
    return tech_list


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("股票数据获取程序启动")
    logger.info("=" * 50)
    
    db = Database()
    tushare = TushareClient()
    
    try:
        logger.info("获取股票基本信息...")
        stock_info_list = tushare.get_stock_info_list()
        
        if not stock_info_list:
            logger.error("获取股票信息失败")
            return
        
        db.insert_stock_info(stock_info_list)
        logger.info(f"成功保存 {len(stock_info_list)} 只股票信息到数据库")
        
        logger.info("获取交易日历...")
        start_date, end_date = tushare.get_trade_dates(TRADE_DAYS)
        
        if not start_date or not end_date:
            logger.error("获取交易日历失败")
            return
        
        logger.info(f"获取 {start_date} 至 {end_date} 的日线数据")
        
        logger.info("获取股票列表...")
        stock_list = tushare.get_stock_list()
        
        if stock_list is None or stock_list.empty:
            logger.error("获取股票列表失败")
            return
        
        total_stocks = len(stock_list)
        logger.info(f"共需获取 {total_stocks} 只股票的数据")
        
        success_count = 0
        fail_count = 0
        total_records = 0
        
        for idx, row in stock_list.iterrows():
            ts_code = row['ts_code']
            stock_name = row['name']
            
            try:
                logger.info(f"[{idx+1}/{total_stocks}] 获取 {ts_code} {stock_name} 的数据...")
                
                daily_data = tushare.get_daily_data(ts_code, start_date, end_date)
                
                if daily_data:
                    inserted = db.insert_daily_data(daily_data)
                    total_records += inserted
                    success_count += 1
                    logger.info(f"  成功获取 {len(daily_data)} 条记录，插入 {inserted} 条")
                    
                    tech_data = calculate_tech_indicators(daily_data)
                    if tech_data:
                        tech_inserted = db.insert_tech_indicators(tech_data)
                        logger.info(f"  计算并插入 {tech_inserted} 条技术指标数据")
                else:
                    logger.info(f"  无数据")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"  获取失败: {e}")
        
        logger.info("=" * 50)
        logger.info("数据获取完成!")
        logger.info(f"成功: {success_count} 只")
        logger.info(f"失败: {fail_count} 只")
        logger.info(f"总记录数: {total_records} 条")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
    finally:
        db.close()
        logger.info("程序退出")


if __name__ == "__main__":
    main()
