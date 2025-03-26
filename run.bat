@echo off
echo 正在启动KIN投资组合再平衡器...

REM 检查Python是否已安装
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python未找到，请确保已安装Python并添加到PATH
    pause
    exit /b 1
)

REM 检查是否需要安装依赖
if not exist "python_deps_installed.txt" (
    echo 首次运行，正在安装Python依赖...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo 安装Python依赖失败
        pause
        exit /b 1
    )
    echo >python_deps_installed.txt
)

REM 启动应用程序
echo 正在启动...
start "" "frontend\target\release\kin-portfolio-rebalancer-gui.exe" 