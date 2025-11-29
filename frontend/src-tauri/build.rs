fn main() {
    tauri_build::build();
    
    // On Windows, if symlink creation fails, copy the library file instead
    // This is a workaround for systems without Developer Mode enabled
    #[cfg(windows)]
    {
        use std::env;
        use std::fs;
        use std::path::PathBuf;
        
        // Only run this for Android targets
        if let Ok(target) = env::var("TARGET") {
            if target.contains("android") {
                let profile = env::var("PROFILE").unwrap_or_else(|_| "debug".to_string());
                let lib_name = "libbilingual_lesson_planner.so";
                
                let source = PathBuf::from("target")
                    .join(&target)
                    .join(&profile)
                    .join(lib_name);
                
                let dest_dir = PathBuf::from("gen")
                    .join("android")
                    .join("app")
                    .join("src")
                    .join("main")
                    .join("jniLibs")
                    .join(&target);
                
                let dest = dest_dir.join(lib_name);
                
                if source.exists() {
                    if let Err(e) = fs::create_dir_all(&dest_dir) {
                        eprintln!("Warning: Failed to create jniLibs directory: {}", e);
                    } else if let Err(e) = fs::copy(&source, &dest) {
                        eprintln!("Warning: Failed to copy library file: {}. You may need to enable Developer Mode or run copy_lib.ps1 manually.", e);
                    }
                }
            }
        }
    }
}
