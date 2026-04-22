"""
回测配置文件
"""
# 数据库配置
DB_PATH = 'e:/other/stock/stock/data/stock_data.db'

# 回测参数
INITIAL_CAPITAL = 100000  # 初始资金（元）
RISK_PER_TRADE = 0.02     # 单笔交易风险（2%）
MAX_POSITIONS = 10        # 最大持仓数量
COMMISSION_RATE = 0.0003  # 佣金费率（万分之三）
STAMP_TAX_RATE = 0.001    # 印花税（千分之一）

# 策略参数
STRATEGY2_PARAMS = {
    'prev_day_pct_chg_min': 2.0,    # 前一日最小涨幅（%）
    'prev_day_pct_chg_max': 8.0,    # 前一日最大涨幅（%）
    'volume_ratio_min': 1.2,        # 最小量比
    'current_day_pct_chg_min': -2.0, # 当日最小涨幅（%）
    'current_day_pct_chg_max': 2.0,  # 当日最大涨幅（%）
}

# 卖出参数
SELL_PARAMS = {
    'min_holding_days': 2,          # 最小持仓天数
    'max_holding_days': 4,          # 最大持仓天数
    'stop_loss': 0.92,              # 止损比例（92%）
    'take_profit': 1.15,            # 止盈比例（115%）
    'std_threshold': 0.5,           # 标准差阈值（中枢相对高位）
}

# 回测期间
BACKTEST_PERIOD = {
    'start_date': '20240101',       # 开始日期
    'end_date': '20241231',         # 结束日期
    'sample_size': 100,             # 快速回测样本大小
}

# 过滤条件
FILTER_CONDITIONS = {
    'min_price': 5.0,               # 最低价格（元）
    'max_price': 200.0,             # 最高价格（元）
    'min_market_cap': 3e9,          # 最小市值（30亿）
    'max_market_cap': 2e11,         # 最大市值（2000亿）
    'min_turnover': 0.03,           # 最小换手率（3%）
}

# 输出配置
OUTPUT_CONFIG = {
    'save_trade_history': True,
    'save_portfolio_value': True,
    'generate_charts': True,
    'output_dir': 'e:/other/stock/stock/TEST',
}