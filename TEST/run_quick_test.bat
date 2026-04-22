@echo off
echo ========================================
echo 策略2快速回测启动
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    echo 请先安装Python并添加到系统PATH
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

REM 检查数据库文件
if not exist "..\data\stock_data.db" (
    echo 警告: 数据库文件不存在
    echo 路径: ..\data\stock_data.db
    echo 请确保数据已正确获取
    echo.
)

REM 运行快速回测
echo 开始运行快速回测...
echo 请稍候...
echo.

python quick_backtest.py

if errorlevel 1 (
    echo.
    echo 回测运行失败
    echo 可能的原因:
    echo 1. 数据库文件不存在或损坏
    echo 2. Python依赖包未安装
    echo 3. 脚本语法错误
    echo.
    echo 建议运行: python check_dependencies.py
) else (
    echo.
    echo 快速回测完成!
    echo 结果文件已保存到当前目录
)

echo.
echo ========================================
echo 按任意键退出...
pause >nul