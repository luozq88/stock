"""
策略2快速回测
简化版本，用于快速验证策略有效性
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class QuickBacktest:
    def __init__(self, db_path, initial_capital=100000):
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trade_history = []
        
    def connect_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_sample_dates(self, sample_size=50):
        """获取样本日期（最近50个交易日）"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT trade_date 
            FROM daily_data 
            ORDER BY trade_date DESC 
            LIMIT ?
        ''', (sample_size,))
        
        dates = [row['trade_date'] for row in cursor.fetchall()]
        dates.sort()  # 按时间顺序排序
        conn.close()
        return dates
    
    def simulate_trades(self, dates):
        """模拟交易"""
        print("开始模拟交易...")
        
        for i, current_date in enumerate(dates):
            if i < 1:  # 需要前一天数据
                continue
                
            prev_date = dates[i-1]
            
            # 获取满足条件的股票
            candidates = self.get_candidates(prev_date, current_date)
            
            if not candidates:
                continue
            
            # 随机选择1-3只股票买入（模拟）
            np.random.seed(42)  # 固定随机种子以便复现
            n_trades = min(np.random.randint(1, 4), len(candidates))
            selected = np.random.choice(candidates, n_trades, replace=False)
            
            for ts_code in selected:
                # 模拟买入
                buy_price = self.get_price(ts_code, current_date)
                if buy_price <= 0:
                    continue
                
                # 计算买入数量（使用2%资金）
                position_size = int(self.capital * 0.02 / buy_price / 100) * 100
                if position_size < 100:
                    position_size = 100
                
                cost = buy_price * position_size
                if cost > self.capital * 0.8:  # 不超过可用资金的80%
                    continue
                
                # 模拟持有2-4天
                hold_days = np.random.randint(2, 5)
                sell_date_idx = min(i + hold_days, len(dates) - 1)
                sell_date = dates[sell_date_idx]
                
                # 模拟卖出价格（基于实际价格加随机波动）
                sell_price = self.get_price(ts_code, sell_date)
                if sell_price <= 0:
                    sell_price = buy_price * np.random.uniform(0.92, 1.15)
                
                # 计算收益
                profit = (sell_price - buy_price) * position_size
                profit_pct = (sell_price / buy_price - 1) * 100
                
                # 记录交易
                self.trade_history.append({
                    'buy_date': current_date,
                    'sell_date': sell_date,
                    'ts_code': ts_code,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'shares': position_size,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'holding_days': hold_days
                })
                
                # 更新资金
                self.capital += profit
        
        print(f"模拟完成，共 {len(self.trade_history)} 笔交易")
    
    def get_candidates(self, prev_date, current_date):
        """获取满足策略条件的候选股票"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 查询满足条件的股票
        query = '''
            SELECT d1.ts_code, 
                   d1.pct_chg as prev_pct_chg,
                   d1.vol as prev_vol,
                   d2.pct_chg as current_pct_chg,
                   t.vol5
            FROM daily_data d1
            JOIN daily_data d2 ON d1.ts_code = d2.ts_code
            LEFT JOIN tech_indicators t ON d1.ts_code = t.ts_code AND t.trade_date = d1.trade_date
            WHERE d1.trade_date = ? 
              AND d2.trade_date = ?
              AND d1.pct_chg BETWEEN 2.0 AND 8.0
              AND d2.pct_chg BETWEEN -2.0 AND 2.0
              AND d1.vol > 0
              AND t.vol5 > 0
              AND d1.vol >= t.vol5 * 1.2
            LIMIT 100
        '''
        
        cursor.execute(query, (prev_date, current_date))
        results = cursor.fetchall()
        
        candidates = [row['ts_code'] for row in results]
        conn.close()
        return candidates
    
    def get_price(self, ts_code, trade_date):
        """获取股票价格"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT close FROM daily_data 
            WHERE ts_code = ? AND trade_date = ?
        ''', (ts_code, trade_date))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def analyze_results(self):
        """分析结果"""
        if not self.trade_history:
            print("没有交易记录")
            return None
        
        df = pd.DataFrame(self.trade_history)
        
        print("\n" + "="*60)
        print("快速回测结果")
        print("="*60)
        
        # 基本统计
        total_trades = len(df)
        winning_trades = len(df[df['profit'] > 0])
        losing_trades = len(df[df['profit'] <= 0])
        
        total_profit = df['profit'].sum()
        total_return_pct = (self.capital / self.initial_capital - 1) * 100
        
        print(f"初始资金: {self.initial_capital:,.2f}元")
        print(f"最终资金: {self.capital:,.2f}元")
        print(f"总收益率: {total_return_pct:.2f}%")
        print(f"总交易次数: {total_trades}次")
        print(f"盈利次数: {winning_trades}次")
        print(f"亏损次数: {losing_trades}次")
        
        if total_trades > 0:
            win_rate = winning_trades / total_trades * 100
            avg_profit_pct = df['profit_pct'].mean()
            avg_holding_days = df['holding_days'].mean()
            
            print(f"胜率: {win_rate:.2f}%")
            print(f"平均单次收益率: {avg_profit_pct:.2f}%")
            print(f"平均持仓天数: {avg_holding_days:.1f}天")
            
            if winning_trades > 0 and losing_trades > 0:
                avg_win = df[df['profit'] > 0]['profit_pct'].mean()
                avg_loss = df[df['profit'] <= 0]['profit_pct'].mean()
                profit_factor = abs(df[df['profit'] > 0]['profit'].sum() / df[df['profit'] <= 0]['profit'].sum())
                
                print(f"平均盈利: {avg_win:.2f}%")
                print(f"平均亏损: {avg_loss:.2f}%")
                print(f"盈亏比: {abs(avg_win/avg_loss):.2f}")
                print(f"盈利因子: {profit_factor:.2f}")
        
        # 收益分布
        print("\n收益分布:")
        print(f"  最大单次盈利: {df['profit_pct'].max():.2f}%")
        print(f"  最大单次亏损: {df['profit_pct'].min():.2f}%")
        print(f"  收益标准差: {df['profit_pct'].std():.2f}%")
        
        # 持仓天数分布
        print("\n持仓天数分布:")
        for days in range(2, 5):
            count = len(df[df['holding_days'] == days])
            if count > 0:
                avg_return = df[df['holding_days'] == days]['profit_pct'].mean()
                print(f"  {days}天持仓: {count}次, 平均收益: {avg_return:.2f}%")
        
        return df
    
    def run(self):
        """运行快速回测"""
        print("策略2快速回测")
        print("="*60)
        
        # 获取样本日期
        dates = self.get_sample_dates(100)  # 最近100个交易日
        print(f"使用 {len(dates)} 个交易日数据进行回测")
        
        # 模拟交易
        self.simulate_trades(dates)
        
        # 分析结果
        df = self.analyze_results()
        
        # 保存结果
        if df is not None:
            df.to_csv('e:/other/stock/stock/TEST/quick_backtest_results.csv', 
                     index=False, encoding='utf-8-sig')
            print(f"\n详细结果已保存到: e:/other/stock/stock/TEST/quick_backtest_results.csv")
        
        return df


def main():
    """主函数"""
    db_path = 'e:/other/stock/stock/data/stock_data.db'
    
    # 检查数据库是否存在
    import os
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        print("请先运行数据获取程序")
        return
    
    # 运行快速回测
    backtest = QuickBacktest(db_path, initial_capital=100000)
    results = backtest.run()
    
    # 策略评估
    print("\n" + "="*60)
    print("策略评估")
    print("="*60)
    
    if results is not None:
        total_return = (backtest.capital / backtest.initial_capital - 1) * 100
        
        if total_return > 20:
            rating = "优秀"
            color = "🟢"
        elif total_return > 10:
            rating = "良好"
            color = "🟡"
        elif total_return > 0:
            rating = "一般"
            color = "🟠"
        else:
            rating = "较差"
            color = "🔴"
        
        print(f"{color} 策略评级: {rating}")
        print(f"{color} 总收益率: {total_return:.2f}%")
        
        win_rate = (len(results[results['profit'] > 0]) / len(results)) * 100
        if win_rate > 60:
            print(f"🟢 胜率优秀: {win_rate:.1f}%")
        elif win_rate > 50:
            print(f"🟡 胜率良好: {win_rate:.1f}%")
        else:
            print(f"🔴 胜率需改进: {win_rate:.1f}%")
        
        # 给出建议
        print("\n建议:")
        if total_return < 10:
            print("  1. 考虑优化买入条件（如前一日涨幅范围）")
            print("  2. 调整持仓天数策略")
            print("  3. 增加止损止盈条件")
        else:
            print("  1. 策略表现良好，可以考虑实盘测试")
            print("  2. 建议进行更长时间的回测")
            print("  3. 考虑增加仓位管理策略")


if __name__ == "__main__":
    main()