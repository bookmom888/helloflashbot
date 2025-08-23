@echo off
echo 视频自动化播放工具启动中...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip list | findstr selenium >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

REM 创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM 启动程序
echo 启动视频自动化播放工具...
python main.py

pause
