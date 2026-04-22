"""
运行回测的主脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

def main():
    print("策略2回测系统")
    print("="*60)
    print("请选择回测模式:")
    print("1. 快速回测（推荐，速度快）")
    print("2. 完整回测（详细，速度慢）")
    print("3. 参数优化回测")
    print("4. 查看回测结果")
    print("5. 退出")
    print("="*60)
    
    choice = input("请输入选择 (1-5): ").strip()
    
    if choice == '1':
        run_quick_backtest()
    elif choice == '2':
        run_full_backtest()
    elif choice == '3':
        run_parameter_optimization()
    elif choice == '4':
        show_results()
    elif choice == '5':
        print("退出回测系统")
    else:
        print("无效选择")

def run_quick_backtest():
    """运行快速回测"""
    print("\n运行快速回测...")
    
    try:
        from quick_backtest import QuickBacktest
        import config
        
        backtest = QuickBacktest(config.DB_PATH, initial_capital=config.INITIAL_CAPITAL)
        results = backtest.run()
        
        if results is not None:
            print("\n快速回测完成！")
            print("详细结果已保存到:")
            print("  e:/other/stock/stock/TEST/quick_backtest_results.csv")
        
    except Exception as e:
        print(f"运行快速回测时出错: {e}")
        print("请检查数据库是否存在且数据完整")

def run_full_backtest():
    """运行完整回测"""
    print("\n运行完整回测...")
    print("注意：完整回测可能需要较长时间")
    
    confirm = input("确定要运行完整回测吗？(y/n): ").strip().lower()
    if confirm != 'y':
        print("取消完整回测")
        return
    
    try:
        from backtest_strategy2 import Strategy2Backtest
        import config
        
        backtest = Strategy2Backtest(config.DB_PATH, initial_capital=config.INITIAL_CAPITAL)
        
        # 设置回测期间
        start_date = config.BACKTEST_PERIOD['start_date']
        end_date = config.BACKTEST_PERIOD['end_date']
        
        print(f"回测期间: {start_date} 到 {end_date}")
        print("开始回测，请耐心等待...")
        
        backtest.run_backtest(start_date, end_date)
        backtest.analyze_results()
        backtest.plot_results()
        backtest.save_results()
        
        print("\n完整回测完成！")
        print("结果已保存到:")
        print("  e:/other/stock/stock/TEST/trade_history.csv")
        print("  e:/other/stock/stock/TEST/portfolio_value.csv")
        print("  e:/other/stock/stock/TEST/backtest_results.png")
        
    except Exception as e:
        print(f"运行完整回测时出错: {e}")
        print("请检查数据库和数据完整性")

def run_parameter_optimization():
    """运行参数优化"""
    print("\n运行参数优化...")
    print("此功能正在开发中")
    
    # 这里可以添加参数网格搜索代码
    print("参数优化功能将在后续版本中提供")

def show_results():
    """显示回测结果"""
    print("\n查看回测结果...")
    
    result_files = [
        'quick_backtest_results.csv',
        'trade_history.csv',
        'portfolio_value.csv',
        'backtest_results.png'
    ]
    
    import os
    for file in result_files:
        filepath = os.path.join('e:/other/stock/stock/TEST', file)
        if os.path.exists(filepath):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (未找到)")
    
    print("\n要查看详细结果，请打开相应的CSV文件")
    print("或查看图表文件: backtest_results.png")

if __name__ == "__main__":
    main()