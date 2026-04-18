#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据获取模块
"""

import sqlite3
import tushare as ts
from datetime import datetime, timedelta

DATABASE_NAME = 'stock.db'


def get_stock_basic():
    """获取股票基本信息"""
    # 初始化tushare
    ts.set_token('your_token_here')  # 需要替换为你自己的tushare token
    pro = ts.pro_api()
    
    # 获取股票基本信息
    df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,market,list_date')
    return df


def get_stock_daily(code, start_date, end_date):
    """获取股票日线数据"""
    ts.set_token('your_token_here')  # 需要替换为你自己的tushare token
    pro = ts.pro_api()
    
    # 获取日线数据
    df = pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
    return df


def fetch_stock_data():
    """获取股票数据并保存到数据库"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # 获取股票基本信息
        print("获取股票基本信息...")
        basic_df = get_stock_basic()
        
        # 保存股票基本信息到数据库
        for index, row in basic_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO stock_basic (code, name, industry, market, list_date)
            VALUES (?, ?, ?, ?, ?)
            ''', (row['ts_code'], row['name'], row['industry'], row['market'], row['list_date']))
        
        conn.commit()
        print(f"保存了{len(basic_df)}条股票基本信息")
        
        # 计算日期范围（最近30天）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        # 获取股票日线数据
        print(f"获取股票日线数据（{start_date} 到 {end_date}）...")
        
        # 只获取前100只股票的数据，避免请求过多
        for i, code in enumerate(basic_df['ts_code'][:100]):
            try:
                daily_df = get_stock_daily(code, start_date, end_date)
                
                # 保存日线数据到数据库
                for index, row in daily_df.iterrows():
                    cursor.execute('''
                    INSERT OR REPLACE INTO stock_daily (code, date, open, high, low, close, volume, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (row['ts_code'], row['trade_date'], row['open'], row['high'], row['low'], 
                          row['close'], row['vol'], row['amount']))
                
                conn.commit()
                print(f"已获取并保存 {code} 的日线数据")
                
                # 避免请求过于频繁
                if (i + 1) % 10 == 0:
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                print(f"获取 {code} 数据失败: {e}")
                continue
        
    except Exception as e:
        print(f"获取数据失败: {e}")
    finally:
        conn.close()
