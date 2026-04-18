#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选股策略模块
"""

import sqlite3
import numpy as np
from datetime import datetime

DATABASE_NAME = 'stock.db'


def get_stock_codes():
    """获取所有股票代码"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT code, name FROM stock_basic')
    stocks = cursor.fetchall()
    
    conn.close()
    return stocks


def get_stock_daily_data(code, days=30):
    """获取股票的日线数据"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT date, open, high, low, close, volume, amount
    FROM stock_daily
    WHERE code = ?
    ORDER BY date DESC
    LIMIT ?
    ''', (code, days))
    
    data = cursor.fetchall()
    conn.close()
    
    # 转换为列表并反转，使日期从早到晚
    data = list(reversed(data))
    return data


def calculate_ma(data, period):
    """计算移动平均线"""
    closes = [d[4] for d in data]  # close价格在第5列
    ma = []
    for i in range(len(closes)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(sum(closes[i-period+1:i+1]) / period)
    return ma


def strategy_ma_golden_cross(code, name):
    """均线金叉策略"""
    data = get_stock_daily_data(code, 30)
    if len(data) < 30:
        return False, "数据不足"
    
    # 计算5日均线和10日均线
    ma5 = calculate_ma(data, 5)
    ma10 = calculate_ma(data, 10)
    
    # 检查是否出现金叉
    if ma5[-2] < ma10[-2] and ma5[-1] > ma10[-1]:
        return True, "5日均线上穿10日均线，形成金叉"
    
    return False, "未出现金叉"


def strategy_volume_expansion(code, name):
    """成交量放大策略"""
    data = get_stock_daily_data(code, 10)
    if len(data) < 10:
        return False, "数据不足"
    
    # 计算成交量平均值
    volumes = [d[5] for d in data]  # 成交量在第6列
    avg_volume = sum(volumes[:-1]) / (len(volumes) - 1)
    
    # 检查今天的成交量是否是平均值的2倍以上
    if volumes[-1] > avg_volume * 2:
        return True, f"成交量放大，今日成交量为{volumes[-1]}，平均成交量为{avg_volume}"
    
    return False, "成交量未明显放大"


def strategy_price_breakout(code, name):
    """价格突破策略"""
    data = get_stock_daily_data(code, 20)
    if len(data) < 20:
        return False, "数据不足"
    
    # 计算最近20天的最高价
    highs = [d[2] for d in data]  # 最高价在第3列
    recent_high = max(highs[:-1])
    
    # 检查今天的收盘价是否突破最近20天的最高价
    if data[-1][4] > recent_high:
        return True, f"价格突破，今日收盘价{data[-1][4]}突破最近20天最高价{recent_high}"
    
    return False, "价格未突破"


def execute_strategies():
    """执行所有选股策略"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # 清空之前的选股结果
    cursor.execute('DELETE FROM strategy_result')
    conn.commit()
    
    # 获取所有股票代码
    stocks = get_stock_codes()
    
    # 执行策略
    strategies = [
        ("均线金叉策略", strategy_ma_golden_cross),
        ("成交量放大策略", strategy_volume_expansion),
        ("价格突破策略", strategy_price_breakout)
    ]
    
    for code, name in stocks:
        for strategy_name, strategy_func in strategies:
            try:
                result, reason = strategy_func(code, name)
                if result:
                    # 保存选股结果
                    cursor.execute('''
                    INSERT INTO strategy_result (strategy_name, code, name, date, reason)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (strategy_name, code, name, datetime.now().strftime('%Y-%m-%d'), reason))
                    conn.commit()
                    print(f"{strategy_name} 选中股票: {code} {name} - {reason}")
            except Exception as e:
                print(f"执行策略时出错: {e}")
                continue
    
    # 打印选股结果统计
    cursor.execute('SELECT strategy_name, COUNT(*) FROM strategy_result GROUP BY strategy_name')
    stats = cursor.fetchall()
    print("\n选股结果统计:")
    for strategy, count in stats:
        print(f"{strategy}: {count} 只股票")
    
    conn.close()
