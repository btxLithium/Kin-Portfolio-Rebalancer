use std::env;
use std::fs;
use std::path::Path;

fn main() {
    // 获取输出目录
    let out_dir = env::var("OUT_DIR").unwrap();
    let profile = env::var("PROFILE").unwrap();

    // 确定字体源目录和目标目录
    let font_source = Path::new("fonts");
    let font_target = Path::new(&out_dir)
        .ancestors()
        .nth(3) // 回溯到 target/{debug|release}
        .unwrap()
        .join("fonts");

    println!("cargo:warning=复制字体文件到: {:?}", font_target);

    // 创建目标目录
    fs::create_dir_all(&font_target).expect("创建字体目录失败");

    // 复制字体文件
    for entry in fs::read_dir(font_source).expect("读取字体目录失败") {
        if let Ok(entry) = entry {
            let source_path = entry.path();
            if source_path.is_file() {
                let target_path = font_target.join(source_path.file_name().unwrap());
                fs::copy(&source_path, &target_path).expect("复制字体文件失败");
                println!("cargo:warning=已复制字体文件: {:?}", target_path);
            }
        }
    }

    // 打印重新构建信息
    println!("cargo:rerun-if-changed=fonts/");
}
