use eframe::egui::{self, FontDefinitions, FontFamily, ViewportBuilder};
use std::fs;
use std::path::Path;
use std::sync::Arc;

mod app;
use app::RebalancerApp;
mod config; // Ensure this is declared if needed

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: ViewportBuilder::default()
            .with_inner_size(egui::vec2(800.0, 600.0))
            .with_min_inner_size(egui::vec2(300.0, 200.0)),
        ..Default::default()
    };

    // Use run_native instead of run_simple_native
    eframe::run_native(
        "KIN Portfolio Rebalancer",
        options,
        // The factory closure now needs to return Ok(...)
        Box::new(|cc| {
            // 加载自定义字体
            let mut fonts = FontDefinitions::default();

            // 尝试不同的字体文件路径
            let font_paths = vec![
                "fonts/OPlusSans3.ttf",          // 相对于根目录
                "../fonts/OPlusSans3.ttf",       // 相对于frontend/target/release
                "frontend/fonts/OPlusSans3.ttf", // 相对于项目根目录
            ];

            let mut font_loaded = false;

            for path in font_paths {
                if Path::new(path).exists() {
                    match fs::read(path) {
                        Ok(font_data) => {
                            println!("成功加载字体: {}", path);
                            // 将字体添加到字体集合中
                            fonts.font_data.insert(
                                "oplusfont".to_owned(),
                                Arc::new(egui::FontData::from_owned(font_data)),
                            );

                            // 将字体设置为比例字体的第一字体
                            fonts
                                .families
                                .get_mut(&FontFamily::Proportional)
                                .unwrap()
                                .insert(0, "oplusfont".to_owned());

                            // 应用字体配置
                            cc.egui_ctx.set_fonts(fonts);
                            font_loaded = true;
                            break;
                        }
                        Err(e) => {
                            eprintln!("尝试路径 {} 失败: {}", path, e);
                        }
                    }
                } else {
                    eprintln!("路径不存在: {}", path);
                }
            }

            if !font_loaded {
                eprintln!("警告: 未能加载自定义字体，将使用默认字体");
            }

            Ok(Box::new(RebalancerApp::new(cc)))
        }),
        //  ^^^^ Use Ok() to wrap the Box<dyn App> in a Result
    )
}
