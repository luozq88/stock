"""
选股策略执行入口
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import LOG_LEVEL, LOG_FORMAT
from strategy import StockStrategy


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("选股策略程序启动")

    strategy = StockStrategy()

    try:
        selected_stocks = strategy.screen_stocks()
        strategy.print_results(selected_stocks)
    except Exception as e:
        logger.error(f"策略执行出错: {e}")
    finally:
        strategy.close()
        logger.info("程序退出")


if __name__ == "__main__":
    main()
