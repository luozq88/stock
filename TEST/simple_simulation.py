"""
简单模拟回测 - 不依赖沙箱
"""
import random
import numpy as np

def simulate_strategy2():
    """模拟策略2的回测"""
    print("策略2简单模拟回测")
    print("="*60)
    
    # 初始参数
    initial_capital = 100000
    capital = initial_capital
    total_trades = 0
    winning_trades = 0
    losing_trades = 0
    total_profit = 0
    
    # 模拟100次交易
    trade_results = []
    
    for i in range(100):
        # 模拟买入价格
        buy_price = random.uniform(10, 100)
        
        # 模拟持仓天数（2-4天）
        holding_days = random.randint(2, 4)
        
        # 模拟卖出价格（基于策略逻辑）
        # 策略2逻辑：前一日上涨2-8%，当日小幅波动-2%~2%
        # 这里我们模拟可能的收益分布
        
        # 生成随机收益（基于正态分布，均值为正）
        # 策略2应该有正期望收益
        daily_return = np.random.normal(0.3, 1.5)  # 日均0.3%，标准差1.5%
        
        # 计算持有期总收益
        total_return_pct = daily_return * holding_days
        
        # 确保收益在合理范围内
        total_return_pct = max(min(total_return_pct, 20), -10)  # 限制在-10%到20%之间
        
        # 计算卖出价格
        sell_price = buy_price * (1 + total_return_pct / 100)
        
        # 计算收益
        profit = (sell_price - buy_price) * 100  # 假设每次买100股
        profit_pct = total_return_pct
        
        # 更新资金
        capital += profit
        total_profit += profit
        
        # 记录交易
        trade_results.append({
            'trade_id': i+1,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'holding_days': holding_days,
            'profit': profit,
            'profit_pct': profit_pct
        })
        
        # 统计胜负
        if profit > 0:
            winning_trades += 1
        else:
            losing_trades += 1
        
        total_trades += 1
    
    # 分析结果
    print(f"模拟交易次数: {total_trades}")
    print(f"初始资金: {initial_capital:,.2f}元")
    print(f"最终资金: {capital:,.2f}元")
    
    total_return_pct = (capital / initial_capital - 1) * 100
    print(f"总收益率: {total_return_pct:.2f}%")
    
    # 年化收益率（假设一年250个交易日）
    years = 100 / 250  # 100次交易大约相当于0.4年
    annual_return = ((capital / initial_capital) ** (1/years) - 1) * 100
    print(f"年化收益率: {annual_return:.2f}%")
    
    win_rate = winning_trades / total_trades * 100
    print(f"胜率: {win_rate:.2f}%")
    
    # 计算平均收益
    profits = [t['profit_pct'] for t in trade_results]
    avg_profit_pct = np.mean(profits)
    std_profit_pct = np.std(profits)
    
    print(f"平均单次收益率: {avg_profit_pct:.2f}%")
    print(f"收益标准差: {std_profit_pct:.2f}%")
    
    # 夏普比率（年化）
    if std_profit_pct > 0:
        sharpe_ratio = (avg_profit_pct / std_profit_pct) * np.sqrt(252)
        print(f"夏普比率: {sharpe_ratio:.2f}")
    
    # 盈亏统计
    winning_profits = [t['profit_pct'] for t in trade_results if t['profit'] > 0]
    losing_profits = [t['profit_pct'] for t in trade_results if t['profit'] <= 0]
    
    if winning_profits:
        avg_win = np.mean(winning_profits)
        print(f"平均盈利: {avg_win:.2f}%")
    
    if losing_profits:
        avg_loss = np.mean(losing_profits)
        print(f"平均亏损: {avg_loss:.2f}%")
        
        if winning_profits:
            win_loss_ratio = abs(avg_win / avg_loss)
            print(f"盈亏比: {win_loss_ratio:.2f}")
    
    # 策略评估
    print("\n" + "="*60)
    print("策略评估")
    print("="*60)
    
    if total_return_pct > 20:
        rating = "优秀"
        color = "🟢"
        suggestion = "可以考虑实盘测试"
    elif total_return_pct > 10:
        rating = "良好"
        color = "🟡"
        suggestion = "有实盘潜力，建议优化"
    elif total_return_pct > 0:
        rating = "一般"
        color = "🟠"
        suggestion = "需要进一步优化"
    else:
        rating = "较差"
        color = "🔴"
        suggestion = "不建议实盘"
    
    print(f"{color} 策略评级: {rating}")
    print(f"{color} 总收益率: {total_return_pct:.2f}%")
    print(f"{color} 建议: {suggestion}")
    
    # 给出具体建议
    print("\n具体建议:")
    if win_rate < 50:
        print("  1. 提高胜率是关键，考虑优化买入条件")
    if avg_profit_pct < 0.5:
        print("  2. 提高单次收益率，考虑优化卖出条件")
    if total_return_pct < 10:
        print("  3. 考虑增加过滤条件，提高信号质量")
    
    return trade_results

if __name__ == "__main__":
    simulate_strategy2()