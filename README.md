<h3 align="center">
  <img
    alt="Image of a colorful hollow hexagon as the logo of this program"
    title="Kin"
    height="160"
    src="assets/kin_logo3.png"
  />
</h3>

<div align="center">
  <h1>Kin Portfolio Rebalancer</h1>
</div>

<p align="center">Cross-platform automated portfolio rebalancer for <a href="https://gate.io/">Gate.io</a><br>跨平台投资组合再平衡机器人，基于Gate.io交易所API</p>

<p align="center">
<img alt="Static Badge" src="https://img.shields.io/badge/license-MIT-blue">
</p>


Read this in [简体中文](https://github.com/btxLithium/Kin-Portfolio-Rebalancer/blob/main/docs/README.Hans.md)

## Features

- Threshold-based Rebalancing: Automatically adjusts the portfolio when asset allocation deviates from the target percentage by a set threshold.
- Cash Flow Rebalancing: Automatically adjusts the portfolio when new stablecoins (USDT or USDC) are received.
- Cross-platform desktop GUI built with Rust (egui).
- (WIP) Python backend handles api keys encryption, communication with Gate.io exchange and rebalancing logic.

## What is a portfolio rebalancer?

A portfolio rebalancer is an automated tool that monitors your cryptocurrency holdings and adjusts them to maintain a predetermined asset allocation. 
It automatically executes trades to buy or sell assets when market fluctuations cause your portfolio to deviate from your target ratios.

## Usage

### Prerequisites

- Python 3.8+
- pip installed

### Use Pre-built executables
TODO:update link
<details>
<summary>Instructions</summary>

1. Download([releases page](https://github.com/jtroo/kanata/releases)) and extract the zip file to any directory

2. Install Python dependencies
   ```
   pip install -r requirements.txt
   ```

3. Launch the application
   - Windows: Double-click `run.bat` or `frontend\target\release\kin-portfolio-rebalancer-gui.exe`
   - Mac/Linux: Run `./run.sh` in a terminal

</details>

### Build it yourself

This project uses the latest Rust stable toolchain. If you installed the
Rust toolchain using `rustup`, e.g. by using the instructions from the
[official website](https://www.rust-lang.org/learn/get-started),
you can get the latest stable toolchain with `rustup update stable`.

<details>
<summary>Instructions</summary>

Build yourself in Linux:

    git clone https://github.com/btxLithium/Kin-Portfolio-Rebalancer 
    cd Kin-Portfolio-Rebalancer
    cd frontend
    cargo build --release


Build yourself in Windows:

    git clone https://github.com/btxLithium/Kin-Portfolio-Rebalancer
    cd .\Kin-Portfolio-Rebalancer\frontend\
    cargo build --release

</details>


## Structure

```
portfolio-rebalancer/
├── backend/         # Python后端
│   ├── api/         # Gate.io API客户端和工具
│   ├── config/      # 配置设置
│   ├── models/      # 数据模型
│   ├── services/    # 再平衡服务
│   └── main.py      # 主程序入口
├── frontend/        # Rust前端
│   ├── src/         # 前端源代码
│   │   ├── main.rs  # 主程序入口
│   │   ├── app.rs   # 应用程序逻辑
│   │   ├── config.rs# 配置文件
│   │   └── lib.rs   # 库文件
│   └── fonts/       # 字体文件目录
│       └── OPlusSans3.ttf # 默认字体

```


### Common Issues

1. If you encounter "Python not found" error:
   - Make sure Python is installed and added to system PATH
   - Or specify the full Python path in run.bat

2. Configuration file:
   - After first run, the configuration file will be saved in your home directory as `.portfolio_rebalancer.json`




## What does the name mean?

"kin" is the reading of the character "鈞", an ancient Chinese unit of weight. 

## Donations

If you'd like to support my work, consider buy me a coffee:

- USDT or USDC Aptos:  
0x675422152a1dcb2eba3011a5f2901d9756ca7be872db10caa3a4dd7f25482e8e  
- USDT or USDC BNB Smart Chain:  
0xbe9c806a872c826fb817f8086aafa26a6104afac  