"""
配置文件
"""
import os

# Tushare配置
TUSHARE_TOKEN = "2f4f7b0dca606122c89b03503ebb70c4b26652328f446848a69e71e2"

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stock_data.db")

# 数据获取配置
TRADE_DAYS = 60  # 获取最近60个交易日的数据

# 请求间隔(秒)，避免API限流
REQUEST_INTERVAL = 0.5

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
