
<div align="center">
  <h1>Kin-Portfolio-Rebalancer</h1>
</div>
<p align="center">跨平台自动化投资组合再平衡机器人，基于Gate.io交易所API</p>

<p align="center">
<img alt="Static Badge" src="https://img.shields.io/badge/license-MIT-blue">
</p>


Read this in [繁體中文](https://github.com/btxLithium/Kin-Portfolio-Rebalancer/blob/main/docs/README.Hant.md)

## Features

- 基于阈值的再平衡：当资产配置偏离目标百分比达到设定阈值时，自动调整投资组合
- 现金流再平衡：当有新的稳定币(USDT或USDC)入账时，自动调整投资组合
- Rust(egui)构建的跨平台简洁桌面GUI
- Python后端处理与Gate.io交易所的通信和再平衡逻辑

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