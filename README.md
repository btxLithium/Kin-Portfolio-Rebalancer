
<div align="center">
  <h1>Kin-Portfolio-Rebalancer</h1>
</div>

<p align="center">Cross-platform automated portfolio rebalancer based on the Gate.io API</p>
<p align="center">跨平台自动化投资组合再平衡机器人，基于Gate.io交易所API</p>

<p align="center">
<img alt="Static Badge" src="https://img.shields.io/badge/license-MIT-blue">
</p>


Read this in [简体中文](https://github.com/btxLithium/Kin-Portfolio-Rebalancer/blob/main/docs/README.Hans.md) | [繁體中文](https://github.com/btxLithium/Kin-Portfolio-Rebalancer/blob/main/docs/README.Hant.md)

## Features

- Threshold-based Rebalancing: Automatically adjusts the portfolio when asset allocation deviates from the target percentage by a set threshold.
- Cash Flow Rebalancing: Automatically adjusts the portfolio when new stablecoins (USDT or USDC) are received.
- Cross-platform desktop GUI built with Rust (egui).
- Python backend handles communication with Gate.io exchange and rebalancing logic.



## 项目结构

```
portfolio-rebalancer/
├── backend/         # Python后端
│   ├── api/         # Gate.io API客户端和工具
│   ├── config/      # 配置设置
│   ├── models/      # 数据模型
│   ├── services/    # 再平衡服务
│   └── main.py      # 主程序入口
├── frontend/        # Rust前端

```




## What does the name mean?

## Donations

If you'd like to support my work, consider buy me a coffee:

- USDT or USDC Aptos:  
0x675422152a1dcb2eba3011a5f2901d9756ca7be872db10caa3a4dd7f25482e8e  
- USDT or USDC BNB Smart Chain:  
0xbe9c806a872c826fb817f8086aafa26a6104afac  