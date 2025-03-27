use eframe::egui::{self, FontDefinitions, FontFamily, ViewportBuilder};
use std::env;
use std::fs;
use std::path::Path;
use std::sync::Arc;

mod app;
use app::RebalancerApp;
mod config;

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: ViewportBuilder::default()
            .with_inner_size(egui::vec2(555.0, 600.0))
            .with_min_inner_size(egui::vec2(300.0, 200.0)),
        ..Default::default()
    };

    eframe::run_native(
        "KIN Portfolio Rebalancer (TestNet Version)",
        options,
        Box::new(|cc| {
            // 加载自定义字体
            let mut fonts = FontDefinitions::default();

            // 尝试将字体从build.rs复制到release目录
            println!("尝试加载字体文件...");

            // 打印当前工作目录
            if let Ok(cwd) = env::current_dir() {
                println!("当前工作目录: {:?}", cwd);
            }

            // 打印可执行文件路径
            if let Ok(exe_path) = env::current_exe() {
                println!("可执行文件路径: {:?}", exe_path);
            }

            // 定义多个可能的字体路径
            let font_paths = [
                "fonts/OPlusSans3.ttf",
                "./fonts/OPlusSans3.ttf",
                "../fonts/OPlusSans3.ttf",
                "frontend/fonts/OPlusSans3.ttf",
                "target/release/fonts/OPlusSans3.ttf",
                "target/debug/fonts/OPlusSans3.ttf",
            ];

            println!("字体搜索路径: {:?}", font_paths);

            let mut font_loaded = false;

            for &path in &font_paths {
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
                eprintln!("未能加载自定义字体，将使用默认字体");
            }

            Ok(Box::new(RebalancerApp::new(cc)))
        }),
    )
}
