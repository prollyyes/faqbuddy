#!/usr/bin/env python3
"""
Neon Database Setup for FAQBuddy
This script sets up connection to an existing Neon PostgreSQL database for new users.
The database is assumed to be already functional and populated.
"""

import os
import sys
import subprocess
import time
import psycopg2
import argparse
from dotenv import load_dotenv

load_dotenv()

# Neon database configuration
DB_NEON_NAME = os.getenv("DB_NEON_NAME", "faqbuddy_db")
DB_NEON_USER = os.getenv("DB_NEON_USER", "db_user")
DB_NEON_PASSWORD = os.getenv("DB_NEON_PASSWORD", "")
DB_NEON_HOST = os.getenv("DB_NEON_HOST", "")
DB_NEON_PORT = os.getenv("DB_NEON_PORT", "5432")

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step_num, total_steps, description):
    """Print a formatted step."""
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")
    print("-" * 40)

def check_neon_credentials():
    """Check if Neon database credentials are provided."""
    print_step(1, 4, "Checking Neon Credentials")
    
    required_vars = {
        "DB_NEON_NAME": DB_NEON_NAME,
        "DB_NEON_USER": DB_NEON_USER,
        "DB_NEON_PASSWORD": DB_NEON_PASSWORD,
        "DB_NEON_HOST": DB_NEON_HOST,
        "DB_NEON_PORT": DB_NEON_PORT
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        print("❌ Missing required Neon database credentials:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these environment variables in your .env file:")
        print("   DB_NEON_NAME=your_neon_database_name")
        print("   DB_NEON_USER=your_neon_username")
        print("   DB_NEON_PASSWORD=your_neon_password")
        print("   DB_NEON_HOST=your_neon_host")
        print("   DB_NEON_PORT=5432")
        return False
    
    print("✅ All Neon credentials are provided")
    print(f"   Database: {DB_NEON_NAME}")
    print(f"   Host: {DB_NEON_HOST}:{DB_NEON_PORT}")
    print(f"   User: {DB_NEON_USER}")
    return True

def test_neon_connection():
    """Test connection to existing Neon database."""
    print_step(2, 4, "Testing Neon Connection")
    
    try:
        # Connect to Neon database
        conn = psycopg2.connect(
            host=DB_NEON_HOST,
            port=DB_NEON_PORT,
            database=DB_NEON_NAME,
            user=DB_NEON_USER,
            password=DB_NEON_PASSWORD,
            sslmode="require"
        )
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("✅ Successfully connected to existing Neon database")
        print(f"   PostgreSQL version: {version[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Neon database: {e}")
        print("\n💡 Please check:")
        print("   - Your Neon database is running")
        print("   - Credentials are correct")
        print("   - Network connectivity")
        print("   - SSL requirements")
        return False

def verify_database():
    """Verify that the existing Neon database has the expected structure."""
    print_step(3, 4, "Verifying Database Structure")
    
    try:
        # Connect to Neon database
        conn = psycopg2.connect(
            host=DB_NEON_HOST,
            port=DB_NEON_PORT,
            database=DB_NEON_NAME,
            user=DB_NEON_USER,
            password=DB_NEON_PASSWORD,
            sslmode="require"
        )
        
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if tables:
            print("✅ Database connection successful")
            print("📋 Tables found:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Check if we have the expected tables
            expected_tables = ['utente', 'corso', 'corso_di_laurea', 'professori', 'materiali']
            found_tables = [table[0].lower() for table in tables]
            
            missing_tables = [table for table in expected_tables if table not in found_tables]
            if missing_tables:
                print(f"⚠️  Some expected tables are missing: {missing_tables}")
                print("   The database might not be fully set up")
            else:
                print("✅ All expected tables are present")
        else:
            print("❌ No tables found in database")
            print("   The database might not be properly initialized")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    
    return True

def update_environment_file():
    """Update .env file with Neon database settings."""
    print_step(4, 4, "Updating Environment")
    
    # Read existing .env file if it exists
    existing_env = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Update with Neon settings
    env_content = f"""# Database Configuration (Neon)
DB_NEON_NAME={DB_NEON_NAME}
DB_NEON_USER={DB_NEON_USER}
DB_NEON_PASSWORD={DB_NEON_PASSWORD}
DB_NEON_HOST={DB_NEON_HOST}
DB_NEON_PORT={DB_NEON_PORT}

# Legacy Database Configuration (for compatibility)
DB_NAME={DB_NEON_NAME}
DB_USER={DB_NEON_USER}
DB_PASSWORD={DB_NEON_PASSWORD}
DB_HOST={DB_NEON_HOST}
DB_PORT={DB_NEON_PORT}

# Pinecone Configuration
PINECONE_API_KEY={existing_env.get('PINECONE_API_KEY', 'your_pinecone_api_key_here')}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file updated with Neon database settings")
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False
    
    return True

def update_pinecone():
    """Update Pinecone with fresh database chunks from Neon."""
    print_step(5, 5, "Updating Pinecone")
    
    try:
        script_path = "backend/src/rag/update_pinecone_db.py"
        print(f"🔄 Running Pinecone update: {script_path}")
        
        # Set environment to use Neon
        env = os.environ.copy()
        env["DB_NAME"] = DB_NEON_NAME
        env["DB_USER"] = DB_NEON_USER
        env["DB_PASSWORD"] = DB_NEON_PASSWORD
        env["DB_HOST"] = DB_NEON_HOST
        env["DB_PORT"] = DB_NEON_PORT
        
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("✅ Pinecone update completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Pinecone update failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running Pinecone update: {e}")
        return False
    
    return True

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='FAQBuddy Neon Database Setup')
    parser.add_argument('--update-vec-db', action='store_true', 
                       help='Update Pinecone vector database with fresh data')
    args = parser.parse_args()
    
    print_header("FAQBuddy Neon Database Setup")
    
    print("This script will set up connection to an existing Neon database.")
    print("The database is assumed to be already functional and populated.")
    print("\nSteps:")
    print("1. Check Neon database credentials")
    print("2. Test connection to existing Neon database")
    print("3. Verify database structure")
    print("4. Update environment file")
    if args.update_vec_db:
        print("5. Update Pinecone with fresh data")
    
    print("\n📋 Required Neon credentials:")
    print("   DB_NEON_NAME - Your Neon database name")
    print("   DB_NEON_USER - Your Neon username")
    print("   DB_NEON_PASSWORD - Your Neon password")
    print("   DB_NEON_HOST - Your Neon host")
    print("   DB_NEON_PORT - Your Neon port (usually 5432)")
    
    if args.update_vec_db:
        print("\n⚠️  Vector Database Update Mode")
        print("   Pinecone will be updated with fresh database chunks.")
        print("   ⚠️  WARNING: This may overwrite existing vectors in the 'db' namespace.")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Setup cancelled")
        return
    
    # Execute steps
    steps = [
        ("Checking Neon Credentials", check_neon_credentials),
        ("Testing Neon Connection", test_neon_connection),
        ("Verifying Database Structure", verify_database),
        ("Updating Environment", update_environment_file),
    ]
    
    # Add Pinecone update step only if --update-vec-db flag is used
    if args.update_vec_db:
        steps.append(("Updating Pinecone", update_pinecone))
    
    for i, (description, step_func) in enumerate(steps, 1):
        if not step_func():
            print(f"\n❌ Setup failed at step {i}: {description}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    print_header("Neon Database Setup Completed Successfully!")
    print("🎉 Your FAQBuddy environment has been configured for Neon!")
    print("\n📊 What was accomplished:")
    print("   ✅ Connected to existing Neon PostgreSQL database")
    print("   ✅ Verified database structure")
    print("   ✅ Environment configured")
    if args.update_vec_db:
        print("   ✅ Pinecone updated with database chunks")
    else:
        print("   ⏭️  Pinecone update skipped (use --update-vec-db to update)")
    print("\n🔧 Database Details:")
    print(f"   - Host: {DB_NEON_HOST}:{DB_NEON_PORT}")
    print(f"   - Database: {DB_NEON_NAME}")
    print(f"   - User: {DB_NEON_USER}")
    print(f"   - SSL: Required")
    print("\n💡 Next steps:")
    print("   - Test your RAG system: python backend/src/rag/run_rag_cli.py")
    print("   - Start backend server: uvicorn src.main:app --reload")
    print("   - Start frontend: npm run dev (in frontend directory)")
    if not args.update_vec_db:
        print("   - To update Pinecone later: python setup_neon_database.py --update-vec-db")
    print("\n🔗 Your application will now use Neon for database operations")

if __name__ == "__main__":
    main() 