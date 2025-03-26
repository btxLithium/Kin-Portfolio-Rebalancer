#!/bin/bash
echo "正在启动KIN投资组合再平衡器..."

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "Python未找到，请确保已安装Python 3"
    exit 1
fi

# 检查是否需要安装依赖
if [ ! -f "python_deps_installed.txt" ]; then
    echo "首次运行，正在安装Python依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "安装Python依赖失败"
        exit 1
    fi
    touch python_deps_installed.txt
fi

# 启动应用程序
echo "正在启动..."
if [ -f "frontend/target/release/kin-portfolio-rebalancer-gui" ]; then
    ./frontend/target/release/kin-portfolio-rebalancer-gui
else
    echo "错误：找不到可执行文件"
    exit 1
fi 