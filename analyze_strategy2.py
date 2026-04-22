"""
分析策略2选出的股票
"""
import sqlite3
import pandas as pd
from collections import Counter
import os

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "data", "stock_data.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def analyze_stocks():
    # 读取选出的股票代码
    with open('selected_stocks_strategy2.txt', 'r', encoding='utf-8') as f:
        selected_codes = [line.strip() for line in f if line.strip()]
    
    print(f"策略2选出的股票数量: {len(selected_codes)}")
    
    # 连接数据库
    conn = connect_db()
    cursor = conn.cursor()
    
    # 1. 分析市场分布
    print("\n" + "="*60)
    print("1. 市场分布分析")
    print("="*60)
    
    market_dist = {
        '科创板(688)': 0,
        '创业板(30)': 0,
        '上海主板(60)': 0,
        '深圳主板(00)': 0,
        '中小板(002/003)': 0
    }
    
    for code in selected_codes:
        if code.startswith('688'):
            market_dist['科创板(688)'] += 1
        elif code.startswith('30'):
            market_dist['创业板(30)'] += 1
        elif code.startswith('60'):
            market_dist['上海主板(60)'] += 1
        elif code.startswith('00'):
            if code.startswith('002') or code.startswith('003'):
                market_dist['中小板(002/003)'] += 1
            else:
                market_dist['深圳主板(00)'] += 1
    
    total = len(selected_codes)
    for market, count in market_dist.items():
        if count > 0:
            percentage = count / total * 100
            print(f"{market}: {count}只 ({percentage:.1f}%)")
    
    # 2. 获取股票基本信息
    print("\n" + "="*60)
    print("2. 行业分布分析")
    print("="*60)
    
    # 获取行业信息
    placeholders = ','.join(['?' for _ in selected_codes])
    cursor.execute(f'''
        SELECT industry, COUNT(*) as count
        FROM stock_info
        WHERE ts_code IN ({placeholders})
        GROUP BY industry
        ORDER BY count DESC
    ''', selected_codes)
    
    industry_results = cursor.fetchall()
    
    if industry_results:
        print("行业分布:")
        for row in industry_results:
            industry = row['industry'] if row['industry'] else '未知'
            count = row['count']
            percentage = count / total * 100
            print(f"  {industry}: {count}只 ({percentage:.1f}%)")
    else:
        print("无法获取行业信息")
    
    # 3. 获取前一日数据统计
    print("\n" + "="*60)
    print("3. 前一日数据统计")
    print("="*60)
    
    # 获取最新交易日
    cursor.execute('SELECT MAX(trade_date) FROM daily_data')
    latest_date = cursor.fetchone()[0]
    
    if latest_date:
        print(f"最新交易日: {latest_date}")
        
        # 获取前一日涨幅和成交量统计
        cursor.execute(f'''
            SELECT 
                AVG(pct_chg) as avg_pct_chg,
                MIN(pct_chg) as min_pct_chg,
                MAX(pct_chg) as max_pct_chg,
                COUNT(*) as count
            FROM daily_data 
            WHERE trade_date = ? AND ts_code IN ({placeholders})
        ''', [latest_date] + selected_codes)
        
        stats = cursor.fetchone()
        if stats and stats['count'] > 0:
            print(f"前一日涨幅统计:")
            print(f"  平均涨幅: {stats['avg_pct_chg']:.2f}%")
            print(f"  最小涨幅: {stats['min_pct_chg']:.2f}%")
            print(f"  最大涨幅: {stats['max_pct_chg']:.2f}%")
            print(f"  有效数据: {stats['count']}只")
    
    # 4. 获取技术指标统计
    print("\n" + "="*60)
    print("4. 技术指标统计")
    print("="*60)
    
    if latest_date:
        cursor.execute(f'''
            SELECT 
                AVG(vol5) as avg_vol5,
                MIN(vol5) as min_vol5,
                MAX(vol5) as max_vol5
            FROM tech_indicators 
            WHERE trade_date = ? AND ts_code IN ({placeholders})
        ''', [latest_date] + selected_codes)
        
        vol_stats = cursor.fetchone()
        if vol_stats:
            print(f"5日成交量均值(vol5)统计:")
            print(f"  平均值: {vol_stats['avg_vol5']:,.0f}")
            print(f"  最小值: {vol_stats['min_vol5']:,.0f}")
            print(f"  最大值: {vol_stats['max_vol5']:,.0f}")
    
    # 5. 显示部分股票详情
    print("\n" + "="*60)
    print("5. 部分股票示例")
    print("="*60)
    
    # 获取前10只股票的详细信息
    sample_codes = selected_codes[:10]
    placeholders_sample = ','.join(['?' for _ in sample_codes])
    
    cursor.execute(f'''
        SELECT s.ts_code, s.name, s.industry,
               d.pct_chg as prev_pct_chg, d.vol as prev_vol,
               t.vol5
        FROM stock_info s
        LEFT JOIN daily_data d ON s.ts_code = d.ts_code AND d.trade_date = ?
        LEFT JOIN tech_indicators t ON s.ts_code = t.ts_code AND t.trade_date = ?
        WHERE s.ts_code IN ({placeholders_sample})
        ORDER BY d.pct_chg DESC
    ''', [latest_date, latest_date] + sample_codes)
    
    sample_stocks = cursor.fetchall()
    
    if sample_stocks:
        print(f"{'代码':<12} {'名称':<10} {'行业':<15} {'前日涨幅%':<10} {'前日成交量':<12} {'VOL5':<12}")
        print("-" * 80)
        for stock in sample_stocks:
            prev_vol_ratio = stock['prev_vol'] / stock['vol5'] if stock['vol5'] and stock['vol5'] > 0 else 0
            print(f"{stock['ts_code']:<12} "
                  f"{stock['name'][:8] if stock['name'] else '未知':<10} "
                  f"{stock['industry'][:12] if stock['industry'] else '未知':<15} "
                  f"{stock['prev_pct_chg']:<10.2f} "
                  f"{stock['prev_vol']:<12,.0f} "
                  f"{stock['vol5']:<12,.0f}")
    
    conn.close()
    
    # 6. 策略有效性分析
    print("\n" + "="*60)
    print("6. 策略有效性分析")
    print("="*60)
    
    print("策略2筛选条件:")
    print("  1. 前一日涨幅: 2% ≤ 涨幅 ≤ 8%")
    print("  2. 前一日量比: 成交量 ≥ VOL5 × 1.2")
    print("  3. 当日涨幅: -2% ≤ 涨幅 ≤ 2%")
    print("\n策略特点:")
    print("  ✓ 选择前一日表现强势的股票")
    print("  ✓ 要求成交量放大（资金关注）")
    print("  ✓ 当日小幅波动（可能蓄势调整）")
    print("  ✓ 避免追高风险")
    
    print("\n投资建议:")
    print("  1. 关注今日涨幅接近0%的股票（蓄势待发）")
    print("  2. 优先选择量比特别高的股票（资金关注度强）")
    print("  3. 注意行业分布，避免过度集中")
    print("  4. 结合市场整体趋势进行选择")

if __name__ == "__main__":
    analyze_stocks()