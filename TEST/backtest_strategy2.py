"""
策略2回测系统
策略逻辑：前一日涨幅2-8% + 量比≥1.2，当日涨幅-2%~2%
持仓周期：2-4个交易日
卖出逻辑：在中枢相对高位卖出
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class Strategy2Backtest:
    def __init__(self, db_path, initial_capital=100000):
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # 当前持仓 {ts_code: {'buy_price': xx, 'buy_date': xx, 'shares': xx}}
        self.trade_history = []  # 交易记录
        self.portfolio_value = []  # 每日 portfolio value
        self.dates = []  # 回测日期
        
    def connect_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_trade_dates(self, start_date, end_date):
        """获取交易日列表"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT trade_date 
            FROM daily_data 
            WHERE trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        ''', (start_date, end_date))
        
        dates = [row['trade_date'] for row in cursor.fetchall()]
        conn.close()
        return dates
    
    def get_stock_universe(self, trade_date):
        """获取指定日期的股票池（所有有数据的股票）"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT ts_code 
            FROM daily_data 
            WHERE trade_date = ?
        ''', (trade_date,))
        
        stocks = [row['ts_code'] for row in cursor.fetchall()]
        conn.close()
        return stocks
    
    def get_stock_data(self, ts_code, trade_date):
        """获取单只股票在指定日期的数据"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取日线数据
        cursor.execute('''
            SELECT * FROM daily_data 
            WHERE ts_code = ? AND trade_date = ?
        ''', (ts_code, trade_date))
        
        daily_data = cursor.fetchone()
        
        # 获取技术指标
        cursor.execute('''
            SELECT * FROM tech_indicators 
            WHERE ts_code = ? AND trade_date = ?
        ''', (ts_code, trade_date))
        
        tech_data = cursor.fetchone()
        
        # 获取股票信息
        cursor.execute('''
            SELECT * FROM stock_info 
            WHERE ts_code = ?
        ''', (ts_code,))
        
        stock_info = cursor.fetchone()
        
        conn.close()
        
        return {
            'daily': dict(daily_data) if daily_data else None,
            'tech': dict(tech_data) if tech_data else None,
            'info': dict(stock_info) if stock_info else None
        }
    
    def get_previous_day_data(self, ts_code, trade_date):
        """获取前一日数据"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取前一个交易日
        cursor.execute('''
            SELECT MAX(trade_date) 
            FROM daily_data 
            WHERE ts_code = ? AND trade_date < ?
        ''', (ts_code, trade_date))
        
        prev_date = cursor.fetchone()[0]
        
        if not prev_date:
            conn.close()
            return None
        
        # 获取前一日日线数据
        cursor.execute('''
            SELECT * FROM daily_data 
            WHERE ts_code = ? AND trade_date = ?
        ''', (ts_code, prev_date))
        
        prev_daily = cursor.fetchone()
        
        # 获取前一日技术指标
        cursor.execute('''
            SELECT * FROM tech_indicators 
            WHERE ts_code = ? AND trade_date = ?
        ''', (ts_code, prev_date))
        
        prev_tech = cursor.fetchone()
        
        conn.close()
        
        return {
            'date': prev_date,
            'daily': dict(prev_daily) if prev_daily else None,
            'tech': dict(prev_tech) if prev_tech else None
        }
    
    def meets_strategy_conditions(self, ts_code, trade_date):
        """检查是否满足策略2的买入条件"""
        # 获取当日数据
        current_data = self.get_stock_data(ts_code, trade_date)
        if not current_data['daily']:
            return False
        
        # 获取前一日数据
        prev_data = self.get_previous_day_data(ts_code, trade_date)
        if not prev_data or not prev_data['daily'] or not prev_data['tech']:
            return False
        
        # 条件1：前一日涨幅在2%-8%之间
        prev_pct_chg = prev_data['daily'].get('pct_chg', 0)
        if prev_pct_chg < 2.0 or prev_pct_chg > 8.0:
            return False
        
        # 条件2：前一日成交量是VOL5的1.2倍以上
        prev_vol = prev_data['daily'].get('vol', 0)
        prev_vol5 = prev_data['tech'].get('vol5', 0)
        
        if prev_vol5 <= 0:
            return False
        
        vol_ratio = prev_vol / prev_vol5
        if vol_ratio < 1.2:
            return False
        
        # 条件3：当日涨幅在-2%~2%之间
        current_pct_chg = current_data['daily'].get('pct_chg', 0)
        if current_pct_chg < -2.0 or current_pct_chg > 2.0:
            return False
        
        # 额外条件：确保数据完整
        current_price = current_data['daily'].get('close', 0)
        if current_price <= 0:
            return False
        
        return True
    
    def calculate_position_size(self, price, risk_per_trade=0.02):
        """计算仓位大小（单只股票不超过总资金的2%）"""
        max_position_value = self.capital * risk_per_trade
        shares = int(max_position_value / price)
        return max(shares, 100)  # 最少100股
    
    def should_sell(self, ts_code, current_date, buy_date, buy_price, current_price):
        """判断是否应该卖出"""
        # 计算持仓天数
        buy_idx = self.dates.index(buy_date) if buy_date in self.dates else -1
        current_idx = self.dates.index(current_date) if current_date in self.dates else -1
        
        if buy_idx == -1 or current_idx == -1:
            return False
        
        holding_days = current_idx - buy_idx
        
        # 条件1：持仓2-4天
        if holding_days < 2:
            return False
        
        if holding_days >= 4:
            return True  # 强制在第4天卖出
        
        # 条件2：中枢相对高位卖出
        # 获取持仓期间的价格数据
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT close FROM daily_data 
            WHERE ts_code = ? AND trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        ''', (ts_code, buy_date, current_date))
        
        prices = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(prices) < 2:
            return False
        
        # 计算中枢（持仓期间的平均价格）
        price_mean = np.mean(prices)
        price_std = np.std(prices)
        
        # 如果当前价格高于中枢1个标准差，认为是相对高位
        if current_price > price_mean + price_std * 0.5:
            return True
        
        # 条件3：止损（-8%）
        if current_price <= buy_price * 0.92:
            return True
        
        # 条件4：止盈（+15%）
        if current_price >= buy_price * 1.15:
            return True
        
        return False
    
    def run_backtest(self, start_date, end_date):
        """运行回测"""
        print("=" * 60)
        print("策略2回测开始")
        print(f"回测期间: {start_date} 到 {end_date}")
        print(f"初始资金: {self.initial_capital:,.2f}元")
        print("=" * 60)
        
        # 获取交易日列表
        self.dates = self.get_trade_dates(start_date, end_date)
        print(f"回测天数: {len(self.dates)}天")
        
        # 每日循环
        for i, current_date in enumerate(self.dates):
            if i % 50 == 0:
                print(f"处理到第{i+1}/{len(self.dates)}天: {current_date}")
            
            # 1. 检查是否需要卖出持仓
            positions_to_sell = []
            for ts_code, position in list(self.positions.items()):
                current_data = self.get_stock_data(ts_code, current_date)
                if not current_data['daily']:
                    continue
                
                current_price = current_data['daily'].get('close', 0)
                buy_price = position['buy_price']
                buy_date = position['buy_date']
                
                if self.should_sell(ts_code, current_date, buy_date, buy_price, current_price):
                    positions_to_sell.append(ts_code)
            
            # 执行卖出
            for ts_code in positions_to_sell:
                position = self.positions.pop(ts_code)
                current_data = self.get_stock_data(ts_code, current_date)
                current_price = current_data['daily'].get('close', position['buy_price'])
                
                sell_value = current_price * position['shares']
                self.capital += sell_value
                
                profit = (current_price - position['buy_price']) * position['shares']
                profit_pct = (current_price / position['buy_price'] - 1) * 100
                
                self.trade_history.append({
                    'date': current_date,
                    'action': 'SELL',
                    'ts_code': ts_code,
                    'price': current_price,
                    'shares': position['shares'],
                    'value': sell_value,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'holding_days': (datetime.strptime(current_date, '%Y%m%d') - 
                                   datetime.strptime(position['buy_date'], '%Y%m%d')).days
                })
            
            # 2. 检查是否可以买入新股票
            # 计算可用资金（最多使用80%的资金）
            available_capital = self.capital * 0.8
            
            # 获取候选股票
            stock_universe = self.get_stock_universe(current_date)
            candidates = []
            
            for ts_code in stock_universe[:500]:  # 限制检查数量以提高速度
                if self.meets_strategy_conditions(ts_code, current_date):
                    current_data = self.get_stock_data(ts_code, current_date)
                    current_price = current_data['daily'].get('close', 0)
                    
                    if current_price > 0 and ts_code not in self.positions:
                        candidates.append({
                            'ts_code': ts_code,
                            'price': current_price,
                            'prev_pct_chg': self.get_previous_day_data(ts_code, current_date)['daily'].get('pct_chg', 0)
                        })
            
            # 按前一日涨幅排序，选择前10只
            candidates.sort(key=lambda x: x['prev_pct_chg'], reverse=True)
            candidates = candidates[:10]
            
            # 买入候选股票
            for candidate in candidates:
                ts_code = candidate['ts_code']
                price = candidate['price']
                
                # 计算可买股数
                shares = self.calculate_position_size(price)
                cost = shares * price
                
                if cost <= available_capital:
                    # 执行买入
                    self.positions[ts_code] = {
                        'buy_price': price,
                        'buy_date': current_date,
                        'shares': shares
                    }
                    
                    self.capital -= cost
                    available_capital -= cost
                    
                    self.trade_history.append({
                        'date': current_date,
                        'action': 'BUY',
                        'ts_code': ts_code,
                        'price': price,
                        'shares': shares,
                        'value': cost
                    })
            
            # 3. 计算当日 portfolio value
            portfolio_value = self.capital
            for ts_code, position in self.positions.items():
                current_data = self.get_stock_data(ts_code, current_date)
                if current_data['daily']:
                    current_price = current_data['daily'].get('close', position['buy_price'])
                    portfolio_value += current_price * position['shares']
            
            self.portfolio_value.append(portfolio_value)
        
        # 回测结束，强制卖出所有持仓
        final_date = self.dates[-1] if self.dates else current_date
        for ts_code, position in list(self.positions.items()):
            current_data = self.get_stock_data(ts_code, final_date)
            current_price = current_data['daily'].get('close', position['buy_price']) if current_data['daily'] else position['buy_price']
            
            sell_value = current_price * position['shares']
            self.capital += sell_value
            
            profit = (current_price - position['buy_price']) * position['shares']
            profit_pct = (current_price / position['buy_price'] - 1) * 100
            
            self.trade_history.append({
                'date': final_date,
                'action': 'SELL',
                'ts_code': ts_code,
                'price': current_price,
                'shares': position['shares'],
                'value': sell_value,
                'profit': profit,
                'profit_pct': profit_pct,
                'holding_days': (datetime.strptime(final_date, '%Y%m%d') - 
                               datetime.strptime(position['buy_date'], '%Y%m%d')).days
            })
        
        self.positions.clear()
        
        print("\n" + "=" * 60)
        print("回测完成")
        print("=" * 60)
    
    def analyze_results(self):
        """分析回测结果"""
        if not self.trade_history:
            print("没有交易记录")
            return
        
        # 转换为DataFrame
        trades_df = pd.DataFrame(self.trade_history)
        
        # 分离买入和卖出记录
        buy_trades = trades_df[trades_df['action'] == 'BUY']
        sell_trades = trades_df[trades_df['action'] == 'SELL']
        
        print("\n" + "=" * 60)
        print("回测结果分析")
        print("=" * 60)
        
        # 基本统计
        print(f"总交易次数: {len(sell_trades)}次")
        print(f"初始资金: {self.initial_capital:,.2f}元")
        print(f"最终资金: {self.capital:,.2f}元")
        
        # 收益率计算
        total_return = (self.capital / self.initial_capital - 1) * 100
        print(f"总收益率: {total_return:.2f}%")
        
        # 年化收益率（假设一年250个交易日）
        if len(self.dates) > 0:
            years = len(self.dates) / 250
            annual_return = ((self.capital / self.initial_capital) ** (1/years) - 1) * 100
            print(f"年化收益率: {annual_return:.2f}%")
        
        # 交易统计
        if len(sell_trades) > 0:
            avg_profit_pct = sell_trades['profit_pct'].mean()
            win_rate = (sell_trades['profit'] > 0).sum() / len(sell_trades) * 100
            avg_holding_days = sell_trades['holding_days'].mean()
            
            print(f"平均单次收益率: {avg_profit_pct:.2f}%")
            print(f"胜率: {win_rate:.2f}%")
            print(f"平均持仓天数: {avg_holding_days:.1f}天")
            
            # 盈亏分布
            winning_trades = sell_trades[sell_trades['profit'] > 0]
            losing_trades = sell_trades[sell_trades['profit'] <= 0]
            
            if len(winning_trades) > 0 and len(losing_trades) > 0:
                avg_win = winning_trades['profit_pct'].mean()
                avg_loss = losing_trades['profit_pct'].mean()
                profit_factor = abs(winning_trades['profit'].sum() / losing_trades['profit'].sum())
                
                print(f"平均盈利: {avg_win:.2f}%")
                print(f"平均亏损: {avg_loss:.2f}%")
                print(f"盈亏比: {abs(avg_win/avg_loss):.2f}")
                print(f"盈利因子: {profit_factor:.2f}")
        
        # 最大回撤
        if len(self.portfolio_value) > 0:
            portfolio_series = pd.Series(self.portfolio_value)
            rolling_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            print(f"最大回撤: {max_drawdown:.2f}%")
        
        # 月度收益
        print("\n月度收益统计:")
        # 这里需要根据实际日期计算月度收益
        
        return trades_df
    
    def plot_results(self):
        """绘制回测结果图表"""
        if len(self.portfolio_value) == 0:
            print("没有数据可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 资金曲线
        axes[0, 0].plot(self.portfolio_value, linewidth=2)
        axes[0, 0].set_title('Portfolio Value Over Time')
        axes[0, 0].set_xlabel('Trading Days')
        axes[0, 0].set_ylabel('Portfolio Value')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 回撤曲线
        portfolio_series = pd.Series(self.portfolio_value)
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max * 100
        
        axes[0, 1].fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
        axes[0, 1].plot(drawdown, color='red', linewidth=1)
        axes[0, 1].set_title('Drawdown')
        axes[0, 1].set_xlabel('Trading Days')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 收益分布直方图
        trades_df = pd.DataFrame(self.trade_history)
        sell_trades = trades_df[trades_df['action'] == 'SELL']
        
        if len(sell_trades) > 0:
            axes[1, 0].hist(sell_trades['profit_pct'], bins=30, alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(x=0, color='red', linestyle='--', linewidth=1)
            axes[1, 0].set_title('Return Distribution')
            axes[1, 0].set_xlabel('Return (%)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 持仓天数分布
        if len(sell_trades) > 0:
            axes[1, 1].hist(sell_trades['holding_days'], bins=20, alpha=0.7, edgecolor='black')
            axes[1, 1].set_title('Holding Days Distribution')
            axes[1, 1].set_xlabel('Holding Days')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('e:/other/stock/stock/TEST/backtest_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("图表已保存到: e:/other/stock/stock/TEST/backtest_results.png")
    
    def save_results(self):
        """保存回测结果"""
        # 保存交易记录
        trades_df = pd.DataFrame(self.trade_history)
        trades_df.to_csv('e:/other/stock/stock/TEST/trade_history.csv', index=False, encoding='utf-8-sig')
        
        # 保存资金曲线
        portfolio_df = pd.DataFrame({
            'date': self.dates[:len(self.portfolio_value)],
            'portfolio_value': self.portfolio_value
        })
        portfolio_df.to_csv('e:/other/stock/stock/TEST/portfolio_value.csv', index=False, encoding='utf-8-sig')
        
        print("交易记录已保存到: e:/other/stock/stock/TEST/trade_history.csv")
        print("资金曲线已保存到: e:/other/stock/stock/TEST/portfolio_value.csv")


def main():
    """主函数"""
    # 数据库路径
    db_path = 'e:/other/stock/stock/data/stock_data.db'
    
    # 创建回测实例
    backtest = Strategy2Backtest(db_path, initial_capital=100000)
    
    # 设置回测期间（最近一年）
    end_date = '20241231'  # 假设当前是2024年底
    start_date = '20240101'
    
    # 运行回测
    backtest.run_backtest(start_date, end_date)
    
    # 分析结果
    trades_df = backtest.analyze_results()
    
    # 绘制图表
    backtest.plot_results()
    
    # 保存结果
    backtest.save_results()
    
    return backtest


if __name__ == "__main__":
    main()