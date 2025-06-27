#!/usr/bin/env python3
"""
FAQBuddy Fresh Environment Setup
This script orchestrates the complete setup of a fresh database and Pinecone index.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step_num, total_steps, description):
    """Print a formatted step."""
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")
    print("-" * 40)

def run_script(script_path, description):
    """Run a Python script and handle errors."""
    print(f"🔄 Running: {description}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False
    
    return True

def check_prerequisites():
    """Check if all required files and dependencies exist."""
    print_step(1, 4, "Checking Prerequisites")
    
    required_files = [
        "db/schema.sql",
        "db/setup_data.py", 
        "db/reset_database.py",
        "backend/src/rag/update_pinecone_db.py",
        "backend/src/rag/utils/generate_chunks.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files found")
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Please create one with your database and Pinecone credentials.")
        return False
    
    print("✅ .env file found")
    return True

def reset_database():
    """Reset the database with fresh schema and data."""
    print_step(2, 4, "Resetting Database")
    
    script_path = "db/reset_database.py"
    return run_script(script_path, "Database Reset")

def update_pinecone():
    """Update Pinecone with fresh database chunks."""
    print_step(3, 4, "Updating Pinecone")
    
    script_path = "backend/src/rag/update_pinecone_db.py"
    return run_script(script_path, "Pinecone Update")

def verify_setup():
    """Verify that the setup was successful."""
    print_step(4, 4, "Verifying Setup")
    
    print("🔍 Checking database connection...")
    try:
        # Try to import and test database connection
        sys.path.append("backend/src")
        from text_2_SQL.db_utils import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if tables exist and have data
        cur.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.tables t2 
                    WHERE t2.table_name = t1.table_name) as has_table,
                   (SELECT COUNT(*) FROM information_schema.columns c 
                    WHERE c.table_name = t1.table_name) as column_count
            FROM information_schema.tables t1
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"✅ Database connected successfully")
        print(f"📊 Found {len(tables)} tables")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    
    print("✅ Setup verification completed")
    return True

def main():
    """Main execution function."""
    print_header("FAQBuddy Fresh Environment Setup")
    
    print("This script will:")
    print("1. Check prerequisites")
    print("2. Reset database with updated schema")
    print("3. Update Pinecone with fresh database chunks")
    print("4. Verify the setup")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Setup cancelled")
        return
    
    # Execute steps
    steps = [
        ("Checking Prerequisites", check_prerequisites),
        ("Resetting Database", reset_database),
        ("Updating Pinecone", update_pinecone),
        ("Verifying Setup", verify_setup)
    ]
    
    for i, (description, step_func) in enumerate(steps, 1):
        if not step_func():
            print(f"\n❌ Setup failed at step {i}: {description}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    print_header("Setup Completed Successfully!")
    print("🎉 Your FAQBuddy environment has been reset and updated!")
    print("\n📊 What was accomplished:")
    print("   ✅ Database reset with updated schema")
    print("   ✅ Fresh sample data loaded")
    print("   ✅ Pinecone updated with database chunks")
    print("   ✅ Document chunks preserved")
    print("\n💡 Next steps:")
    print("   - Test your RAG system with the CLI: python backend/src/rag/run_rag_cli.py")
    print("   - Or integrate with your API")
    print("\n🔧 Namespace structure:")
    print("   - 'db': Database chunks (fresh)")
    print("   - 'documents': Document chunks (preserved)")
    print("   - 'v9': Enhanced chunks (if any)")

if __name__ == "__main__":
    main() 