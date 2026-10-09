#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod models;
mod path_detector;
mod sync_engine;
mod commands;

use commands::*;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            discover_configs,
            load_all_providers,
            save_single_provider,
            delete_single_provider,
            analyze_duplicates,
            open_folder,
        ])
        .run(tauri::generate_context!())
        .expect("运行 Tauri 应用程序时发生错误");
}
