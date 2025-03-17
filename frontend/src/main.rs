use eframe::egui;
use portfolio_rebalancer_gui::app::RebalancerApp;

fn main() -> Result<(), eframe::Error> {
    // Set up logging
    env_logger::init();

    let options = eframe::NativeOptions {
        initial_window_size: Some(egui::vec2(800.0, 600.0)),
        min_window_size: Some(egui::vec2(600.0, 400.0)),
        ..Default::default()
    };

    eframe::run_native(
        "KIN Portfolio Rebalancer",
        options,
        Box::new(|cc| Box::new(RebalancerApp::new(cc)))
    )
}