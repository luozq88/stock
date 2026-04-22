"""
生成策略评估报告
"""
import pandas as pd
import numpy as np
from datetime import datetime
import os

class StrategyReport:
    def __init__(self, results_file=None):
        self.results_file = results_file
        self.results = None
        self.report_data = {}
        
    def load_results(self, filepath):
        """加载回测结果"""
        if os.path.exists(filepath):
            self.results = pd.read_csv(filepath)
            self.results_file = filepath
            return True
        else:
            print(f"文件不存在: {filepath}")
            return False
    
    def analyze_trades(self):
        """分析交易记录"""
        if self.results is None:
            print("没有结果数据")
            return
        
        df = self.results
        
        # 基本统计
        total_trades = len(df)
        winning_trades = len(df[df['profit'] > 0])
        losing_trades = len(df[df['profit'] <= 0])
        
        total_profit = df['profit'].sum()
        avg_profit_pct = df['profit_pct'].mean()
        win_rate = winning_trades / total_trades * 100
        
        # 盈亏统计
        if winning_trades > 0:
            avg_win = df[df['profit'] > 0]['profit_pct'].mean()
            max_win = df[df['profit'] > 0]['profit_pct'].max()
        else:
            avg_win = 0
            max_win = 0
            
        if losing_trades > 0:
            avg_loss = df[df['profit'] <= 0]['profit_pct'].mean()
            max_loss = df[df['profit'] <= 0]['profit_pct'].min()
        else:
            avg_loss = 0
            max_loss = 0
        
        # 持仓天数统计
        avg_holding_days = df['holding_days'].mean()
        
        # 风险指标
        returns_std = df['profit_pct'].std()
        if avg_profit_pct != 0:
            sharpe_ratio = avg_profit_pct / returns_std * np.sqrt(252)  # 年化夏普比率
        else:
            sharpe_ratio = 0
        
        # 保存分析结果
        self.report_data['basic_stats'] = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_profit': total_profit,
            'avg_profit_pct': avg_profit_pct,
            'win_rate': win_rate
        }
        
        self.report_data['profit_stats'] = {
            'avg_win': avg_win,
            'max_win': max_win,
            'avg_loss': avg_loss,
            'max_loss': max_loss,
            'profit_factor': abs(df[df['profit'] > 0]['profit'].sum() / df[df['profit'] <= 0]['profit'].sum()) if losing_trades > 0 else 0
        }
        
        self.report_data['holding_stats'] = {
            'avg_holding_days': avg_holding_days,
            'min_holding_days': df['holding_days'].min(),
            'max_holding_days': df['holding_days'].max()
        }
        
        self.report_data['risk_metrics'] = {
            'returns_std': returns_std,
            'sharpe_ratio': sharpe_ratio
        }
        
        return self.report_data
    
    def evaluate_strategy(self):
        """评估策略表现"""
        if not self.report_data:
            self.analyze_trades()
        
        stats = self.report_data['basic_stats']
        profit_stats = self.report_data['profit_stats']
        risk_metrics = self.report_data['risk_metrics']
        
        # 评分系统
        score = 0
        max_score = 100
        
        # 1. 胜率评分（30分）
        win_rate = stats['win_rate']
        if win_rate > 60:
            score += 30
        elif win_rate > 55:
            score += 25
        elif win_rate > 50:
            score += 20
        elif win_rate > 45:
            score += 15
        else:
            score += 10
        
        # 2. 平均收益率评分（30分）
        avg_return = stats['avg_profit_pct']
        if avg_return > 2.0:
            score += 30
        elif avg_return > 1.5:
            score += 25
        elif avg_return > 1.0:
            score += 20
        elif avg_return > 0.5:
            score += 15
        else:
            score += 10
        
        # 3. 盈亏比评分（20分）
        if profit_stats['avg_win'] != 0 and profit_stats['avg_loss'] != 0:
            win_loss_ratio = abs(profit_stats['avg_win'] / profit_stats['avg_loss'])
            if win_loss_ratio > 2.0:
                score += 20
            elif win_loss_ratio > 1.5:
                score += 16
            elif win_loss_ratio > 1.2:
                score += 12
            elif win_loss_ratio > 1.0:
                score += 8
            else:
                score += 4
        
        # 4. 夏普比率评分（20分）
        sharpe = risk_metrics['sharpe_ratio']
        if sharpe > 1.5:
            score += 20
        elif sharpe > 1.0:
            score += 16
        elif sharpe > 0.5:
            score += 12
        elif sharpe > 0:
            score += 8
        else:
            score += 4
        
        # 总体评级
        rating_pct = score / max_score * 100
        
        if rating_pct >= 90:
            rating = "卓越"
            color = "🟢"
            action = "强烈建议实盘"
        elif rating_pct >= 80:
            rating = "优秀"
            color = "🟢"
            action = "建议实盘测试"
        elif rating_pct >= 70:
            rating = "良好"
            color = "🟡"
            action = "可考虑实盘"
        elif rating_pct >= 60:
            rating = "一般"
            color = "🟠"
            action = "需要优化"
        elif rating_pct >= 50:
            rating = "较差"
            color = "🔴"
            action = "不建议实盘"
        else:
            rating = "很差"
            color = "🔴"
            action = "需要重新设计"
        
        evaluation = {
            'score': score,
            'max_score': max_score,
            'rating_pct': rating_pct,
            'rating': rating,
            'color': color,
            'action': action,
            'details': {
                'win_rate_score': min(30, win_rate/2),
                'avg_return_score': min(30, avg_return * 15),
                'sharpe_score': min(20, sharpe * 13.33)
            }
        }
        
        self.report_data['evaluation'] = evaluation
        return evaluation
    
    def generate_report(self, output_file=None):
        """生成详细报告"""
        if not self.report_data:
            self.analyze_trades()
            self.evaluate_strategy()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'e:/other/stock/stock/TEST/strategy_report_{timestamp}.txt'
        
        report_lines = []
        
        # 报告头部
        report_lines.append("=" * 70)
        report_lines.append("策略2评估报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 70)
        
        # 基本信息
        report_lines.append("\n一、基本信息")
        report_lines.append("-" * 40)
        report_lines.append(f"结果文件: {self.results_file}")
        report_lines.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 交易统计
        stats = self.report_data['basic_stats']
        report_lines.append("\n二、交易统计")
        report_lines.append("-" * 40)
        report_lines.append(f"总交易次数: {stats['total_trades']}次")
        report_lines.append(f"盈利次数: {stats['winning_trades']}次")
        report_lines.append(f"亏损次数: {stats['losing_trades']}次")
        report_lines.append(f"胜率: {stats['win_rate']:.2f}%")
        report_lines.append(f"平均单次收益率: {stats['avg_profit_pct']:.2f}%")
        report_lines.append(f"总收益: {stats['total_profit']:,.2f}元")
        
        # 盈亏分析
        profit_stats = self.report_data['profit_stats']
        report_lines.append("\n三、盈亏分析")
        report_lines.append("-" * 40)
        report_lines.append(f"平均盈利: {profit_stats['avg_win']:.2f}%")
        report_lines.append(f"最大盈利: {profit_stats['max_win']:.2f}%")
        report_lines.append(f"平均亏损: {profit_stats['avg_loss']:.2f}%")
        report_lines.append(f"最大亏损: {profit_stats['max_loss']:.2f}%")
        report_lines.append(f"盈亏比: {abs(profit_stats['avg_win']/profit_stats['avg_loss']):.2f}" if profit_stats['avg_loss'] != 0 else "盈亏比: N/A")
        report_lines.append(f"盈利因子: {profit_stats['profit_factor']:.2f}")
        
        # 持仓分析
        holding_stats = self.report_data['holding_stats']
        report_lines.append("\n四、持仓分析")
        report_lines.append("-" * 40)
        report_lines.append(f"平均持仓天数: {holding_stats['avg_holding_days']:.1f}天")
        report_lines.append(f"最短持仓天数: {holding_stats['min_holding_days']}天")
        report_lines.append(f"最长持仓天数: {holding_stats['max_holding_days']}天")
        
        # 风险指标
        risk_metrics = self.report_data['risk_metrics']
        report_lines.append("\n五、风险指标")
        report_lines.append("-" * 40)
        report_lines.append(f"收益标准差: {risk_metrics['returns_std']:.2f}%")
        report_lines.append(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
        
        # 策略评估
        evaluation = self.report_data['evaluation']
        report_lines.append("\n六、策略评估")
        report_lines.append("-" * 40)
        report_lines.append(f"综合评分: {evaluation['score']}/{evaluation['max_score']}")
        report_lines.append(f"评分百分比: {evaluation['rating_pct']:.1f}%")
        report_lines.append(f"{evaluation['color']} 策略评级: {evaluation['rating']}")
        report_lines.append(f"{evaluation['color']} 建议行动: {evaluation['action']}")
        
        # 详细评分
        report_lines.append("\n七、详细评分")
        report_lines.append("-" * 40)
        report_lines.append(f"胜率评分: {evaluation['details']['win_rate_score']:.1f}/30")
        report_lines.append(f"收益率评分: {evaluation['details']['avg_return_score']:.1f}/30")
        report_lines.append(f"夏普比率评分: {evaluation['details']['sharpe_score']:.1f}/20")
        
        # 建议
        report_lines.append("\n八、优化建议")
        report_lines.append("-" * 40)
        
        if evaluation['rating_pct'] >= 80:
            report_lines.append("1. 策略表现优秀，可以考虑实盘测试")
            report_lines.append("2. 建议从小资金开始，逐步增加")
            report_lines.append("3. 建立完善的风险控制体系")
        elif evaluation['rating_pct'] >= 60:
            report_lines.append("1. 策略有改进空间，建议优化参数")
            report_lines.append("2. 考虑增加过滤条件（如市值、换手率）")
            report_lines.append("3. 调整持仓天数和卖出条件")
        else:
            report_lines.append("1. 策略需要重新设计或大幅优化")
            report_lines.append("2. 建议分析失败交易的原因")
            report_lines.append("3. 考虑结合其他策略或因子")
        
        # 风险提示
        report_lines.append("\n九、风险提示")
        report_lines.append("-" * 40)
        report_lines.append("1. 回测表现不代表实盘表现")
        report_lines.append("2. 市场环境变化可能导致策略失效")
        report_lines.append("3. 建议定期评估和优化策略")
        report_lines.append("4. 投资有风险，决策需谨慎")
        
        # 报告尾部
        report_lines.append("\n" + "=" * 70)
        report_lines.append("报告结束")
        report_lines.append("=" * 70)
        
        # 写入文件
        report_content = "\n".join(report_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"报告已生成: {output_file}")
        
        # 同时在控制台显示摘要
        print("\n" + "=" * 60)
        print("策略评估摘要")
        print("=" * 60)
        print(f"胜率: {stats['win_rate']:.1f}%")
        print(f"平均收益率: {stats['avg_profit_pct']:.2f}%")
        print(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
        print(f"综合评分: {evaluation['score']}/{evaluation['max_score']} ({evaluation['rating_pct']:.1f}%)")
        print(f"{evaluation['color']} 评级: {evaluation['rating']}")
        print(f"{evaluation['color']} 建议: {evaluation['action']}")
        
        return output_file


def main():
    """主函数"""
    print("策略评估报告生成器")
    print("="*60)
    
    # 检查结果文件
    result_files = [
        'quick_backtest_results.csv',
        'trade_history.csv'
    ]
    
    available_files = []
    for file in result_files:
        filepath = f'e:/other/stock/stock/TEST/{file}'
        if os.path.exists(filepath):
            available_files.append((file, filepath))
    
    if not available_files:
        print("未找到回测结果文件")
        print("请先运行回测系统")
        return
    
    print("找到以下结果文件:")
    for i, (file, filepath) in enumerate(available_files, 1):
        print(f"{i}. {file}")
    
    choice = input(f"\n请选择要分析的文件 (1-{len(available_files)}): ").strip()
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(available_files):
            selected_file, filepath = available_files[choice_idx]
        else:
            print("无效选择")
            return
    except:
        print("无效输入")
        return
    
    # 生成报告
    print(f"\n分析文件: {selected_file}")
    
    report_generator = StrategyReport()
    if report_generator.load_results(filepath):
        report_generator.analyze_trades()
        report_generator.evaluate_strategy()
        report_file = report_generator.generate_report()
        
        print(f"\n详细报告已保存到: {report_file}")
        print("\n建议:")
        print("1. 查看报告了解策略详细表现")
        print("2. 根据评估结果决定是否实盘")
        print("3. 如需优化，可调整策略参数")


if __name__ == "__main__":
    main()