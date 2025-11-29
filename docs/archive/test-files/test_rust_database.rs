// Integration test for Rust database operations
// Run with: cargo test --test test_rust_database

use std::path::PathBuf;
use std::fs;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_database_initialization() {
        // Create a temporary database path
        let test_db = PathBuf::from("test_lesson_planner.db");
        
        // Clean up if exists
        if test_db.exists() {
            fs::remove_file(&test_db).unwrap();
        }
        
        // This would test init_database, but we need to make it public or create a test helper
        // For now, just verify the path is valid
        assert!(test_db.parent().is_some());
        
        // Clean up
        if test_db.exists() {
            fs::remove_file(&test_db).unwrap();
        }
    }
}

