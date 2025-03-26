use anyhow::{Result, anyhow};
use egui::{Align, Button, Color32, Label, Layout, RichText, Spinner, TextEdit, Ui};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::thread;

use crate::config::{Config, PortfolioAllocation};

pub struct RebalancerApp {
    config: Config,
    api_key: String,
    api_secret: String,
    config_path: PathBuf,
    backend_process: Option<Child>,
    status: String,
    is_running: bool,
    error_message: Option<String>,

    // Portfolio allocation editor
    portfolio_editor: PortfolioAllocationEditor,

    // UI state
    show_portfolio_editor: bool,
    show_api_settings: bool,
}

#[derive(Default)]
struct PortfolioAllocationEditor {
    btc_allocation: String,
    eth_allocation: String,
    ltc_allocation: String,
    usdt_allocation: String,
    rebalance_threshold: String,
    min_usdt_inflow: String,
}

impl PortfolioAllocationEditor {
    // Calculate USDT allocation based on other allocations
    fn calculate_usdt(&self) -> f64 {
        let btc = self.btc_allocation.parse::<f64>().unwrap_or(0.0);
        let eth = self.eth_allocation.parse::<f64>().unwrap_or(0.0);
        let ltc = self.ltc_allocation.parse::<f64>().unwrap_or(0.0);

        let usdt = 100.0 - btc - eth - ltc;
        if usdt < 0.0 { 0.0 } else { usdt }
    }

    // Get USDT allocation as a string
    fn get_usdt_display(&self) -> String {
        format!("{:.1}", self.calculate_usdt())
    }
}

impl RebalancerApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        // Set up the custom fonts
        let fonts = egui::FontDefinitions::default();

        // Configure dark mode
        let mut style = (*cc.egui_ctx.style()).clone();
        style.visuals = egui::Visuals::dark();
        cc.egui_ctx.set_style(style);

        // Try to load config
        let config_path = Self::get_config_path();
        let config = Self::load_config(&config_path).unwrap_or_default();

        // Initialize portfolio editor with current config values
        let portfolio_editor = PortfolioAllocationEditor {
            btc_allocation: config.portfolio_allocation.btc_usdt.to_string(),
            eth_allocation: config.portfolio_allocation.eth_usdt.to_string(),
            ltc_allocation: config.portfolio_allocation.ltc_usdt.to_string(),
            usdt_allocation: config.portfolio_allocation.usdt.to_string(),
            rebalance_threshold: config.rebalance_threshold.to_string(),
            min_usdt_inflow: config.min_usdt_inflow.to_string(),
        };

        Self {
            config,
            api_key: String::new(),
            api_secret: String::new(),
            config_path,
            backend_process: None,
            status: "Stopped".to_string(),
            is_running: false,
            error_message: None,
            portfolio_editor,
            show_portfolio_editor: true,
            show_api_settings: false,
        }
    }

    fn get_config_path() -> PathBuf {
        dirs::home_dir()
            .unwrap_or_default()
            .join(".portfolio_rebalancer.json")
    }

    fn load_config(path: &PathBuf) -> Result<Config> {
        if path.exists() {
            let config_str = fs::read_to_string(path)?;
            let config: Config = serde_json::from_str(&config_str)?;
            Ok(config)
        } else {
            Err(anyhow!("Config file not found"))
        }
    }

    fn save_config(&self) -> Result<()> {
        let config_json = serde_json::to_string_pretty(&self.config)?;
        let mut file = fs::File::create(&self.config_path)?;
        file.write_all(config_json.as_bytes())?;
        Ok(())
    }

    fn start_backend(&mut self) -> Result<()> {
        // Save config first
        self.save_config()?;

        // 尝试找到Python解释器
        let python_cmd = if cfg!(windows) {
            if std::path::Path::new("python.exe").exists() {
                "python.exe" // 如果打包了Python解释器
            } else {
                "python" // 使用系统Python
            }
        } else {
            "python"
        };

        // Start Python backend
        let mut cmd = Command::new(python_cmd);

        // 检查后端路径
        let backend_main = if std::path::Path::new("backend/main.py").exists() {
            cmd.arg("backend/main.py"); // 直接运行脚本
        } else {
            cmd.arg("-m").arg("backend.main"); // 作为模块运行
        };

        cmd.arg("--config").arg(&self.config_path);

        match cmd.spawn() {
            Ok(child) => {
                self.backend_process = Some(child);
                self.status = "Running".to_string();
                self.is_running = true;
                Ok(())
            }
            Err(e) => {
                self.error_message = Some(format!("Failed to start backend: {}", e));
                Err(anyhow!("Failed to start backend: {}", e))
            }
        }
    }

    fn stop_backend(&mut self) {
        if let Some(mut child) = self.backend_process.take() {
            let _ = child.kill();
            self.status = "Stopped".to_string();
            self.is_running = false;
        }
    }

    fn update_config_from_editor(&mut self) -> Result<()> {
        // Parse and validate portfolio allocations
        let btc = self
            .portfolio_editor
            .btc_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid BTC allocation"))?;
        let eth = self
            .portfolio_editor
            .eth_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid ETH allocation"))?;
        let ltc = self
            .portfolio_editor
            .ltc_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid LTC allocation"))?;

        // Calculate USDT as 100% minus other allocations
        let usdt = self.portfolio_editor.calculate_usdt();

        // Ensure we have positive allocations
        if btc < 0.0 || eth < 0.0 || ltc < 0.0 || usdt < 0.0 {
            return Err(anyhow!("Allocations must be positive"));
        }

        // Parse threshold values
        let threshold = self
            .portfolio_editor
            .rebalance_threshold
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid rebalance threshold"))?;
        let min_inflow = self
            .portfolio_editor
            .min_usdt_inflow
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid minimum USDT inflow"))?;

        // Update config
        self.config.portfolio_allocation = PortfolioAllocation {
            btc_usdt: btc,
            eth_usdt: eth,
            ltc_usdt: ltc,
            usdt,
        };
        self.config.rebalance_threshold = threshold;
        self.config.min_usdt_inflow = min_inflow;

        self.save_config()?;
        Ok(())
    }

    fn update_api_settings(&mut self) -> Result<()> {
        if self.api_key.is_empty() || self.api_secret.is_empty() {
            return Err(anyhow!("API key and secret cannot be empty"));
        }

        self.config.api_key = self.api_key.clone();
        self.config.api_secret = self.api_secret.clone();

        self.save_config()?;
        self.api_key.clear();
        self.api_secret.clear();

        Ok(())
    }
}

impl eframe::App for RebalancerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.show_portfolio_editor = !self.show_api_settings;

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                ui.heading("KIN Portfolio Rebalancer");
            });

            ui.add_space(20.0);

            // Status display
            ui.horizontal(|ui| {
                ui.label("Status:");
                let status_color = if self.is_running {
                    Color32::GREEN
                } else {
                    Color32::RED
                };
                ui.colored_label(status_color, &self.status);
            });

            ui.add_space(10.0);

            // Error message (if any)
            if let Some(error) = &self.error_message {
                ui.label(RichText::new(error).color(Color32::RED));
                ui.add_space(10.0);

                if ui.button("Clear Error").clicked() {
                    self.error_message = None;
                }

                ui.add_space(10.0);
            }

            // Main buttons
            ui.horizontal(|ui| {
                if !self.is_running {
                    if ui.button("Start Rebalancer").clicked() {
                        match self.start_backend() {
                            Ok(_) => {
                                self.error_message = None;
                            }
                            Err(e) => {
                                self.error_message = Some(e.to_string());
                            }
                        }
                    }
                } else {
                    if ui.button("Stop Rebalancer").clicked() {
                        self.stop_backend();
                    }
                }

                if ui.button("Settings").clicked() {
                    self.show_api_settings = !self.show_api_settings;
                }
            });

            ui.add_space(20.0);

            // Portfolio allocation editor
            if self.show_portfolio_editor {
                ui.group(|ui| {
                    ui.heading("Portfolio Allocation(投资组合配置)");
                    ui.add_space(10.0);

                    // Asset allocations
                    ui.columns(2, |columns| {
                        columns[0].label("Bitcoin (BTC):");
                        columns[1].text_edit_singleline(&mut self.portfolio_editor.btc_allocation);
                    });

                    ui.columns(2, |columns| {
                        columns[0].label("Ethereum (ETH):");
                        columns[1].text_edit_singleline(&mut self.portfolio_editor.eth_allocation);
                    });

                    ui.columns(2, |columns| {
                        columns[0].label("Litecoin (LTC):");
                        columns[1].text_edit_singleline(&mut self.portfolio_editor.ltc_allocation);
                    });

                    ui.columns(2, |columns| {
                        columns[0].label("USDT (auto-calculated):");
                        let usdt_display = self.portfolio_editor.get_usdt_display();
                        columns[1].label(RichText::new(&usdt_display).strong());
                        // Update the usdt_allocation field with the calculated value
                        self.portfolio_editor.usdt_allocation = usdt_display;
                    });

                    ui.add_space(10.0);

                    // Rebalancing settings
                    ui.heading("Rebalancing Settings(再平衡设置)");
                    ui.add_space(5.0);

                    ui.columns(2, |columns| {
                        columns[0].label("Rebalance Threshold(再平衡阈值) (%):");
                        columns[1]
                            .text_edit_singleline(&mut self.portfolio_editor.rebalance_threshold);
                    });

                    ui.columns(2, |columns| {
                        columns[0].label("Min USDT Inflow(最小USDT流入):");
                        columns[1].text_edit_singleline(&mut self.portfolio_editor.min_usdt_inflow);
                    });

                    ui.add_space(10.0);

                    // Save button
                    if ui.button("Save Portfolio Settings").clicked() {
                        match self.update_config_from_editor() {
                            Ok(_) => {
                                self.error_message = None;
                                self.show_portfolio_editor = false;
                            }
                            Err(e) => {
                                self.error_message = Some(e.to_string());
                            }
                        }
                    }
                });
            }

            // API settings
            if self.show_api_settings {
                ui.group(|ui| {
                    ui.heading("Gate.io API Settings");
                    ui.add_space(10.0);

                    ui.horizontal(|ui| {
                        ui.label("API Key:");
                        ui.text_edit_singleline(&mut self.api_key);
                    });

                    ui.horizontal(|ui| {
                        ui.label("API Secret:");
                        let password = TextEdit::singleline(&mut self.api_secret)
                            .password(true)
                            .desired_width(ui.available_width() - 100.0);
                        ui.add(password);
                    });

                    ui.add_space(10.0);

                    if ui.button("Save API Settings").clicked() {
                        match self.update_api_settings() {
                            Ok(_) => {
                                self.error_message = None;
                                self.show_api_settings = false;
                            }
                            Err(e) => {
                                self.error_message = Some(e.to_string());
                            }
                        }
                    }
                });
            }

            // Current portfolio display (simplified)
            ui.add_space(20.0);
            if self.is_running {
                ui.group(|ui| {
                    ui.heading("Current Portfolio Status");
                    ui.label("Portfolio status display would be here in a completed application.");
                    ui.label("(Would show current allocations, balances, etc.)");
                });
            }

            // Footer
            ui.with_layout(Layout::bottom_up(Align::Center), |ui| {
                ui.add_space(10.0);
                ui.label("KIN Portfolio Rebalancer v0.1.0");
                ui.add_space(5.0);
            });
        });
    }

    fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>) {
        // Stop backend on exit
        self.stop_backend();
    }
}
