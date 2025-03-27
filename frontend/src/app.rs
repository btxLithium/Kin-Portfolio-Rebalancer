use anyhow::{anyhow, Result};
use eframe::egui::{self, Align, Button, Color32, Grid, Layout, RichText, TextEdit, Vec2};
use std::fs;
use std::io::Write; // 仅保留用于保存配置的Write
use std::path::PathBuf;
use std::process::{Child, Command};

use crate::config::{Config, PortfolioAllocation};

pub struct RebalancerApp {
    config: Config,
    api_key: String,
    api_secret: String,
    config_path: PathBuf,
    backend_process: Option<Child>, // Keep handle to manage the process
    status: String,
    is_running: bool,
    error_message: Option<String>,

    // Removed backend output state:
    // backend_output_receiver: Option<Receiver<String>>,
    // portfolio_summary_output: Vec<String>,

    // Portfolio allocation editor
    portfolio_editor: PortfolioAllocationEditor,

    // UI state
    show_portfolio_editor: bool,
    show_api_settings: bool,
}

#[derive(Default)]
struct PortfolioAllocationEditor {
    BTC_USDT_allocation: String,
    ETH_USDT_allocation: String,
    LTC_USDT_allocation: String,
    USDT_allocation: String, // 保留为只读显示项
    rebalance_threshold: String,
    min_usdt_inflow: String,
}

impl PortfolioAllocationEditor {
    // Calculate USDT allocation based on other allocations
    fn calculate_usdt(&self) -> f64 {
        let btc = self.BTC_USDT_allocation.parse::<f64>().unwrap_or(0.0);
        let eth = self.ETH_USDT_allocation.parse::<f64>().unwrap_or(0.0);
        let ltc = self.LTC_USDT_allocation.parse::<f64>().unwrap_or(0.0);

        let crypto_total = btc + eth + ltc;
        let usdt = if crypto_total > 100.0 {
            0.0
        } else {
            (100.0 - crypto_total).max(0.0) // Ensure it's not negative due to float issues
        };
        usdt
    }

    // Get USDT allocation as a string for display
    fn get_usdt_display(&self) -> String {
        format!("{:.1}", self.calculate_usdt())
    }
}

impl RebalancerApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let mut style = (*cc.egui_ctx.style()).clone();
        style.visuals = egui::Visuals::dark();
        cc.egui_ctx.set_style(style);

        let config_path = Self::get_config_path();
        let config = Self::load_config(&config_path).unwrap_or_else(|e| {
            println!(
                "Failed to load config ({:?}): {}, using default.",
                config_path, e
            );
            Config::default()
        });

        let portfolio_editor = PortfolioAllocationEditor {
            BTC_USDT_allocation: config.portfolio_allocation.BTC_USDT.to_string(),
            ETH_USDT_allocation: config.portfolio_allocation.ETH_USDT.to_string(),
            LTC_USDT_allocation: config.portfolio_allocation.LTC_USDT.to_string(),
            USDT_allocation: format!("{:.1}", config.portfolio_allocation.USDT),
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
            // Removed backend output state initialization
            // backend_output_receiver: None,
            // portfolio_summary_output: Vec::new(),
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
            serde_json::from_str(&config_str).map_err(|e| anyhow!("Failed to parse config: {}", e))
        } else {
            Err(anyhow!("Config file not found at {:?}", path))
        }
    }

    fn save_config(&self) -> Result<()> {
        let config_json = serde_json::to_string_pretty(&self.config)?;
        let mut file = fs::File::create(&self.config_path)?;
        file.write_all(config_json.as_bytes())?;
        Ok(())
    }

    fn start_backend(&mut self) -> Result<()> {
        if let Err(e) = self.update_config_from_editor() {
            self.error_message = Some(format!("Failed to save config before start: {}", e));
            return Err(e);
        }
        self.error_message = None; // Clear previous config errors

        // 确保已保存配置
        if let Err(e) = self.save_config() {
            self.error_message = Some(format!("Failed to save config: {}", e));
            return Err(e);
        }

        // 在Windows上使用PowerShell启动后端
        if cfg!(windows) {
            let mut cmd = Command::new("powershell");
            cmd.arg("-NoExit"); // 保持窗口打开
            cmd.arg("-Command");

            // 构建Python命令
            let python_cmd = format!(
                "cd ..; python -m backend.main --config \"{}\"",
                self.config_path.display()
            );

            cmd.arg(&python_cmd);

            // 启动进程
            match cmd.spawn() {
                Ok(_) => {
                    // 不保存子进程的句柄，因为它在独立窗口中运行
                    self.status = "Running (External)".to_string();
                    self.is_running = true;
                    self.error_message = None;
                    println!("Backend started in external PowerShell window.");
                    Ok(())
                }
                Err(e) => {
                    self.status = "Error".to_string();
                    self.is_running = false;
                    self.error_message = Some(format!("Failed to start backend: {}", e));
                    Err(anyhow!("Failed to start backend: {}", e))
                }
            }
        } else if cfg!(target_os = "linux") || cfg!(target_os = "macos") {
            // 在Linux/macOS上使用终端启动后端
            let terminal_cmd = if cfg!(target_os = "macos") {
                "open -a Terminal"
            } else {
                "x-terminal-emulator" // Linux通用终端启动器
            };

            let mut cmd = Command::new(terminal_cmd);

            // 构建要在终端中运行的命令
            let python_cmd = format!(
                "cd \"$(dirname \"$(dirname \"$0\")\")\" && python -m backend.main --config \"{}\"",
                self.config_path.display()
            );

            if cfg!(target_os = "macos") {
                cmd.arg("-e");
                cmd.arg(&python_cmd);
            } else {
                cmd.arg("-e");
                cmd.arg(&format!("bash -c '{}'", python_cmd));
            }

            // 启动进程
            match cmd.spawn() {
                Ok(_) => {
                    // 不保存子进程的句柄
                    self.status = "Running (External)".to_string();
                    self.is_running = true;
                    self.error_message = None;
                    println!("Backend started in external terminal window.");
                    Ok(())
                }
                Err(e) => {
                    self.status = "Error".to_string();
                    self.is_running = false;
                    self.error_message = Some(format!("Failed to start backend: {}", e));
                    Err(anyhow!("Failed to start backend: {}", e))
                }
            }
        } else {
            Err(anyhow!("Unsupported operating system"))
        }
    }

    fn stop_backend(&mut self) {
        // 由于后端现在运行在独立窗口中，我们只需更新状态
        self.status = "Stopped (Close Terminal to Stop Backend)".to_string();
        self.is_running = false;
        self.backend_process = None;
        println!("To completely stop the backend, close the terminal window.");
    }

    fn update_config_from_editor(&mut self) -> Result<()> {
        let btc = self
            .portfolio_editor
            .BTC_USDT_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid BTC allocation"))?;
        let eth = self
            .portfolio_editor
            .ETH_USDT_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid ETH allocation"))?;
        let ltc = self
            .portfolio_editor
            .LTC_USDT_allocation
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid LTC allocation"))?;

        if btc < 0.0 || eth < 0.0 || ltc < 0.0 {
            return Err(anyhow!("Allocations cannot be negative."));
        }
        let crypto_total = btc + eth + ltc;
        if crypto_total > 100.0 {
            return Err(anyhow!(
                "Sum of BTC, ETH, LTC allocations ({:.1}%) cannot exceed 100%.",
                crypto_total
            ));
        }

        // USDT allocation is calculated automatically
        let usdt = (100.0 - crypto_total).max(0.0);

        let threshold = self
            .portfolio_editor
            .rebalance_threshold
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid rebalance threshold"))?;
        if threshold < 0.0 {
            return Err(anyhow!("Rebalance threshold cannot be negative."));
        }

        let min_inflow = self
            .portfolio_editor
            .min_usdt_inflow
            .parse::<f64>()
            .map_err(|_| anyhow!("Invalid minimum USDT inflow"))?;
        if min_inflow < 0.0 {
            return Err(anyhow!("Minimum USDT inflow cannot be negative."));
        }

        self.config.portfolio_allocation = PortfolioAllocation {
            BTC_USDT: btc,
            ETH_USDT: eth,
            LTC_USDT: ltc,
            USDT: usdt,
        };
        self.config.rebalance_threshold = threshold;
        self.config.min_usdt_inflow = min_inflow;
        self.portfolio_editor.USDT_allocation = format!("{:.1}", usdt); // Update display value

        self.save_config()?;
        println!("Configuration saved successfully.");
        Ok(())
    }

    fn update_api_settings(&mut self) -> Result<()> {
        if self.api_key.trim().is_empty() || self.api_secret.trim().is_empty() {
            return Err(anyhow!("API key and secret cannot be empty."));
        }
        // TODO: Add encryption here if needed before saving
        self.config.api_key = self.api_key.trim().to_string();
        self.config.api_secret = self.api_secret.trim().to_string();
        self.save_config()?;
        self.api_key.clear();
        self.api_secret.clear();
        println!("API settings saved successfully.");
        Ok(())
    }
}

// --- eframe::App Implementation ---
impl eframe::App for RebalancerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // --- Check if backend process exited unexpectedly ---
        if self.is_running {
            let mut process_exited = false;
            let mut exit_status_str = String::new();

            if let Some(child) = &mut self.backend_process {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        // Process has exited
                        println!(
                            "Backend process exited unexpectedly with status: {}",
                            status
                        );
                        exit_status_str = format!("Stopped (Exited: {})", status);
                        process_exited = true;
                    }
                    Ok(None) => { /* Process still running, do nothing */ }
                    Err(e) => {
                        // Error trying to check status
                        eprintln!("Error checking backend process status: {}", e);
                        exit_status_str = format!("Error ({})", e);
                        process_exited = true; // Treat error as if it exited
                    }
                }
            } else {
                // Should not happen if is_running is true, but handle defensively
                println!("Inconsistent state: is_running=true but backend_process is None.");
                exit_status_str = "Error (Inconsistent)".to_string();
                process_exited = true;
            }

            if process_exited {
                self.is_running = false;
                self.backend_process = None; // Clear the handle
                self.status = exit_status_str;
                // Optionally add to error_message:
                // self.error_message = Some("Backend process stopped unexpectedly.".to_string());
                ctx.request_repaint(); // Request repaint to show updated status
            }
        }

        // --- Removed: Processing backend output from channel ---

        // --- UI Definition ---
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                ui.heading("KIN Portfolio Rebalancer (TestNet Version)");
            });
            ui.add_space(15.0);

            // Status Display
            ui.horizontal(|ui| {
                ui.label("Status:");
                let status_color = match self.status.as_str() {
                    "Running" => Color32::GREEN,
                    "Starting" => Color32::YELLOW,
                    s if s.starts_with("Error") => Color32::RED,
                    s if s.starts_with("Stopped") => Color32::GRAY,
                    _ => Color32::LIGHT_GRAY,
                };
                ui.colored_label(status_color, &self.status);
            });
            ui.add_space(5.0);

            // Error Message Display
            if let Some(error) = &self.error_message {
                ui.colored_label(Color32::RED, error);
                if ui.button("Clear Error").clicked() {
                    self.error_message = None;
                }
                ui.add_space(5.0);
            }

            // Main Control Buttons
            ui.horizontal(|ui| {
                if !self.is_running {
                    let start_button = ui.add_enabled(self.backend_process.is_none(), Button::new("START Rebalancer"));
                    if start_button.clicked() {
                        self.status = "Starting".to_string();
                        match self.start_backend() {
                            Ok(_) => { /* Status updated in start_backend */ }
                            Err(_) => { /* Status updated in start_backend */ }
                        }
                    }
                } else {
                    if ui.button("STOP Rebalancer").clicked() {
                        self.stop_backend(); // Status updated in stop_backend
                    }
                }
                ui.separator();
                if ui.selectable_label(self.show_api_settings, "API Settings").clicked() {
                    self.show_api_settings = true;
                    self.show_portfolio_editor = false;
                }
                if ui.selectable_label(self.show_portfolio_editor, "Portfolio Config").clicked() {
                    self.show_portfolio_editor = true;
                    self.show_api_settings = false;
                }
            });
            ui.add_space(10.0);
            ui.separator();
            ui.add_space(10.0);

            // Conditional UI Sections (Portfolio Editor / API Settings)
            if self.show_portfolio_editor {
                ui.group(|ui| {
                     ui.heading("Portfolio Allocation (投资组合配置)");
                     ui.label("Target percentages for 3x leveraged pairs and USDT.");
                     ui.add_space(10.0);
                     let text_edit_width = 60.0;
                     Grid::new("allocation_grid").num_columns(3).spacing([10.0, 4.0]).striped(true).show(ui, |ui| {
                         ui.label("BTC_USDT (3x Long):");
                         ui.add(TextEdit::singleline(&mut self.portfolio_editor.BTC_USDT_allocation).desired_width(text_edit_width)); ui.label("%"); ui.end_row();
                         ui.label("ETH_USDT (3x Long):");
                         ui.add(TextEdit::singleline(&mut self.portfolio_editor.ETH_USDT_allocation).desired_width(text_edit_width)); ui.label("%"); ui.end_row();
                         ui.label("LTC_USDT (3x Long):");
                         ui.add(TextEdit::singleline(&mut self.portfolio_editor.LTC_USDT_allocation).desired_width(text_edit_width)); ui.label("%"); ui.end_row();
                         ui.label("USDT (剩余):");
                         let usdt_display = self.portfolio_editor.get_usdt_display();
                         ui.label(RichText::new(format!("{}%", usdt_display)).strong()); ui.label(""); ui.end_row();
                     });
                     ui.add_space(10.0); ui.separator(); ui.add_space(10.0);
                     ui.heading("Rebalancing Settings (再平衡设置)"); ui.add_space(5.0);
                     Grid::new("rebalancing_grid").num_columns(2).spacing([10.0, 4.0]).striped(true).show(ui, |ui| {
                         ui.label("Threshold Deviation (%):");
                         ui.add(TextEdit::singleline(&mut self.portfolio_editor.rebalance_threshold).desired_width(text_edit_width)); ui.end_row();
                         ui.label("Min Cash Inflow (USDT):");
                         ui.add(TextEdit::singleline(&mut self.portfolio_editor.min_usdt_inflow).desired_width(text_edit_width)); ui.end_row();
                     });
                     ui.add_space(15.0);
                     let save_button = ui.button("Save Portfolio Config");
                     if save_button.clicked() {
                         match self.update_config_from_editor() {
                             Ok(_) => { self.error_message = Some("Portfolio config saved.".to_string()); } // Use error field briefly
                             Err(e) => { self.error_message = Some(e.to_string()); }
                         }
                     }
                     save_button.on_hover_text("Saves settings to the config file. The backend needs to be restarted (or dynamically reload config) to use new settings.");
                 });
            }

            if self.show_api_settings {
                 ui.group(|ui| {
                    ui.heading("Gate.io API Settings (TestNet)");
                    ui.label("These are stored locally in the config file.");
                    ui.add_space(10.0);
                    ui.horizontal(|ui| {
                        ui.label(RichText::new("API Key:").strong());
                        ui.with_layout(Layout::right_to_left(egui::Align::Center), |ui|{
                            ui.add_sized(Vec2::new(ui.available_width() * 0.7, 0.0), TextEdit::singleline(&mut self.api_key)); });
                    });
                    ui.horizontal(|ui| {
                        ui.label(RichText::new("API Secret:").strong());
                        ui.with_layout(Layout::right_to_left(egui::Align::Center), |ui|{
                            let password = TextEdit::singleline(&mut self.api_secret).password(true).desired_width(ui.available_width() * 0.7); ui.add(password); });
                    });
                    ui.add_space(10.0);
                    ui.horizontal(|ui| {
                        ui.label("Configured API Key:");
                        let display_key = if self.config.api_key.len() > 6 { format!("...{}", &self.config.api_key[self.config.api_key.len() - 6..]) }
                                          else if self.config.api_key.is_empty() { "Not set".to_string() }
                                          else { "******".to_string() };
                        ui.label(display_key).on_hover_text(&self.config.api_key);
                    });
                    ui.add_space(10.0);
                    if ui.button("Save API Settings").clicked() {
                        match self.update_api_settings() {
                            Ok(_) => {
                                self.show_api_settings = false; self.show_portfolio_editor = true;
                                self.error_message = Some("API settings saved.".to_string()); // Use error field briefly
                            }
                            Err(e) => { self.error_message = Some(e.to_string()); }
                        }
                    }
                 });
            }


            // Add link only when running
            if self.is_running {
                ui.add_space(10.0);
                ui.hyperlink_to(
                    "View TestNet Positions on Gate.io",
                    "https://www.gate.io/en/testnet/futures_trade/USDT/BTC_USDT",
                );
            }

            // Footer
            ui.with_layout(Layout::bottom_up(Align::Center), |ui| {
                ui.add_space(5.0); ui.separator(); ui.add_space(5.0);
                ui.label(format!("KIN Portfolio Rebalancer v0.1.0 | Config: {}", self.config_path.display()));
                ui.add_space(5.0);
            });
        }); // End CentralPanel
    }

    fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>) {
        println!("Exit requested. Stopping backend...");
        self.stop_backend();
        println!("Backend stopped. Exiting.");
    }
}
