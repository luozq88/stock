"""
检查依赖包
"""
import sys
import subprocess
import pkg_resources

def check_package(package_name):
    """检查包是否安装"""
    try:
        dist = pkg_resources.get_distribution(package_name)
        print(f"✓ {package_name} ({dist.version})")
        return True
    except pkg_resources.DistributionNotFound:
        print(f"✗ {package_name} (未安装)")
        return False

def install_package(package_name):
    """安装包"""
    print(f"正在安装 {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package_name} 安装失败")
        return False

def main():
    print("检查回测系统依赖包")
    print("="*60)
    
    required_packages = [
        'pandas',
        'numpy',
        'matplotlib',
        'sqlite3'  # Python内置，不需要安装
    ]
    
    optional_packages = [
        'scipy',
        'seaborn',
        'tqdm'
    ]
    
    missing_packages = []
    
    # 检查必需包
    print("\n必需包:")
    for package in required_packages:
        if not check_package(package):
            missing_packages.append(package)
    
    # 检查可选包
    print("\n可选包:")
    for package in optional_packages:
        check_package(package)
    
    # 安装缺失的包
    if missing_packages:
        print(f"\n发现 {len(missing_packages)} 个缺失的包")
        install_all = input("是否自动安装所有缺失的包？(y/n): ").strip().lower()
        
        if install_all == 'y':
            for package in missing_packages:
                install_package(package)
        else:
            print("请手动安装缺失的包:")
            for package in missing_packages:
                print(f"  pip install {package}")
    
    # 检查数据库
    print("\n" + "="*60)
    print("检查数据库...")
    
    import os
    db_path = 'e:/other/stock/stock/data/stock_data.db'
    
    if os.path.exists(db_path):
        print(f"✓ 数据库文件存在: {db_path}")
        
        # 检查数据库大小
        try:
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"  数据库大小: {size_mb:.2f} MB")
            
            if size_mb < 10:
                print("  ⚠️ 数据库可能太小，请确保数据完整")
            else:
                print("  ✓ 数据库大小正常")
        except:
            print("  ⚠️ 无法获取数据库大小")
    else:
        print(f"✗ 数据库文件不存在: {db_path}")
        print("  请先运行数据获取程序")
    
    # 检查数据表
    print("\n" + "="*60)
    print("检查数据表...")
    
    if os.path.exists(db_path):
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            tables = ['daily_data', 'tech_indicators', 'stock_info']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    print(f"✓ 表 {table} 存在")
                else:
                    print(f"✗ 表 {table} 不存在")
            
            # 检查数据量
            print("\n检查数据量:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,} 条记录")
            
            conn.close()
        except Exception as e:
            print(f"检查数据库时出错: {e}")
    
    print("\n" + "="*60)
    print("依赖检查完成")
    
    if not missing_packages and os.path.exists(db_path):
        print("✓ 所有依赖已满足，可以运行回测")
        print("\n运行回测:")
        print("  python run_backtest.py")
    else:
        print("⚠️ 请先解决上述问题再运行回测")

if __name__ == "__main__":
    main()