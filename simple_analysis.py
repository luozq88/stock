"""
简单分析策略2选出的股票
"""
import os

def analyze_stock_codes():
    # 读取选出的股票代码
    with open('selected_stocks_strategy2.txt', 'r', encoding='utf-8') as f:
        selected_codes = [line.strip() for line in f if line.strip()]
    
    print(f"策略2选出的股票数量: {len(selected_codes)}")
    
    # 1. 分析市场分布
    print("\n" + "="*60)
    print("1. 市场分布分析")
    print("="*60)
    
    market_dist = {
        '科创板(688开头)': 0,
        '创业板(30开头)': 0,
        '上海主板(60开头)': 0,
        '深圳主板(000开头)': 0,
        '中小板(002/003开头)': 0,
        '其他': 0
    }
    
    for code in selected_codes:
        if code.startswith('688'):
            market_dist['科创板(688开头)'] += 1
        elif code.startswith('30'):
            market_dist['创业板(30开头)'] += 1
        elif code.startswith('60'):
            market_dist['上海主板(60开头)'] += 1
        elif code.startswith('000'):
            market_dist['深圳主板(000开头)'] += 1
        elif code.startswith('002') or code.startswith('003'):
            market_dist['中小板(002/003开头)'] += 1
        else:
            market_dist['其他'] += 1
    
    total = len(selected_codes)
    for market, count in market_dist.items():
        if count > 0:
            percentage = count / total * 100
            print(f"{market}: {count}只 ({percentage:.1f}%)")
    
    # 2. 分析代码特征
    print("\n" + "="*60)
    print("2. 代码特征分析")
    print("="*60)
    
    # 统计不同开头的股票
    code_prefixes = {}
    for code in selected_codes:
        prefix = code[:3]
        code_prefixes[prefix] = code_prefixes.get(prefix, 0) + 1
    
    # 按数量排序
    sorted_prefixes = sorted(code_prefixes.items(), key=lambda x: x[1], reverse=True)
    
    print("代码前缀分布（前10位）:")
    for i, (prefix, count) in enumerate(sorted_prefixes[:10], 1):
        percentage = count / total * 100
        print(f"  {i:2d}. {prefix}开头: {count:3d}只 ({percentage:.1f}%)")
    
    # 3. 策略逻辑分析
    print("\n" + "="*60)
    print("3. 策略逻辑分析")
    print("="*60)
    
    print("策略2筛选条件:")
    print("  ✓ 前一日涨幅: 2% ≤ 涨幅 ≤ 8%")
    print("  ✓ 前一日量比: 成交量 ≥ VOL5 × 1.2")
    print("  ✓ 当日涨幅: -2% ≤ 涨幅 ≤ 2%")
    
    print("\n策略特点:")
    print("  • 选择前一日表现强势的股票（有上涨动力）")
    print("  • 要求成交量放大（有资金关注）")
    print("  • 当日小幅波动（可能处于调整或蓄势阶段）")
    print("  • 避免追高风险（不选当日大涨的股票）")
    
    # 4. 投资建议
    print("\n" + "="*60)
    print("4. 投资建议")
    print("="*60)
    
    print("基于代码分布的分析:")
    
    # 科创板分析
    kcb_count = market_dist['科创板(688开头)']
    if kcb_count > 0:
        kcb_pct = kcb_count / total * 100
        print(f"  • 科创板({kcb_count}只, {kcb_pct:.1f}%):")
        print("    - 特点: 高科技、高成长、高波动")
        print("    - 风险: 估值较高，波动性大")
        print("    - 建议: 适合风险偏好较高的投资者")
    
    # 创业板分析
    cyb_count = market_dist['创业板(30开头)']
    if cyb_count > 0:
        cyb_pct = cyb_count / total * 100
        print(f"  • 创业板({cyb_count}只, {cyb_pct:.1f}%):")
        print("    - 特点: 成长型企业，创新性强")
        print("    - 风险: 业绩波动大，政策敏感")
        print("    - 建议: 关注行业前景和公司基本面")
    
    # 主板分析
    mainboard_count = market_dist['上海主板(60开头)'] + market_dist['深圳主板(000开头)'] + market_dist['中小板(002/003开头)']
    if mainboard_count > 0:
        mainboard_pct = mainboard_count / total * 100
        print(f"  • 主板({mainboard_count}只, {mainboard_pct:.1f}%):")
        print("    - 特点: 相对稳定，行业龙头多")
        print("    - 风险: 成长性可能较低")
        print("    - 建议: 适合稳健型投资者")
    
    # 5. 重点关注
    print("\n" + "="*60)
    print("5. 重点关注")
    print("="*60)
    
    print("建议重点关注以下类型的股票:")
    print("  1. 今日涨幅接近0%的股票（蓄势待发）")
    print("  2. 前一日量比特别高的股票（资金关注度强）")
    print("  3. 属于热门行业的股票（如新能源、半导体等）")
    print("  4. 市值适中的股票（流动性好）")
    
    # 6. 示例股票
    print("\n" + "="*60)
    print("6. 示例股票（前20只）")
    print("="*60)
    
    print("代码             市场板块")
    print("-" * 40)
    for i, code in enumerate(selected_codes[:20], 1):
        if code.startswith('688'):
            market = "科创板"
        elif code.startswith('30'):
            market = "创业板"
        elif code.startswith('60'):
            market = "沪主板"
        elif code.startswith('000'):
            market = "深主板"
        elif code.startswith('002') or code.startswith('003'):
            market = "中小板"
        else:
            market = "其他"
        
        print(f"{code:<15} {market}")

if __name__ == "__main__":
    analyze_stock_codes()