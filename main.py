#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主脚本文件，用于获取股票数据并保存到SQLite数据库，同时执行选股策略
"""

import os
import sqlite3
import time
from datetime import datetime

from data_fetcher import fetch_stock_data
from strategy import execute_strategies

# 配置参数
DATABASE_NAME = 'stock.db'


def init_database():
    """初始化数据库，创建必要的表"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # 创建股票基本信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_basic (
        code TEXT PRIMARY KEY,
        name TEXT,
        industry TEXT,
        market TEXT,
        list_date TEXT
    )
    ''')
    
    # 创建股票日线数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        amount REAL,
        FOREIGN KEY (code) REFERENCES stock_basic (code)
    )
    ''')
    
    # 创建选股结果表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS strategy_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_name TEXT,
        code TEXT,
        name TEXT,
        date TEXT,
        reason TEXT,
        FOREIGN KEY (code) REFERENCES stock_basic (code)
    )
    ''')
    
    conn.commit()
    conn.close()


def main():
    """主函数"""
    print("开始执行股票数据获取和选股策略...")
    
    # 初始化数据库
    init_database()
    
    # 获取股票数据
    print("正在获取股票数据...")
    fetch_stock_data()
    
    # 执行选股策略
    print("正在执行选股策略...")
    execute_strategies()
    
    print("执行完成！")


if __name__ == '__main__':
    main()
