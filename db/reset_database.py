#!/usr/bin/env python3
"""
Database Reset Script for FAQBuddy
This script completely resets the database with the updated schema and fresh data.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import subprocess
import time

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        sys.exit(1)
    
    print("✅ Environment variables loaded")

def drop_and_create_db():
    """Drop existing database and create a fresh one."""
    print(f"🗑️  Dropping database {DB_NAME} (if exists)...")
    
    try:
        # Connect to postgres database to drop/create our target database
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Terminate active connections to our database
        cur.execute(f"""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity
            WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();
        """)
        
        # Drop and recreate database
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
        print(f"📝 Creating fresh database {DB_NAME}...")
        cur.execute(f"CREATE DATABASE {DB_NAME};")
        
        cur.close()
        conn.close()
        print("✅ Database reset complete")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)

def run_schema_sql():
    """Execute the updated schema.sql file."""
    print("📋 Running updated schema.sql...")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    cmd = [
        "psql",
        "-h", DB_HOST,
        "-p", str(DB_PORT),
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", schema_path
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error running schema.sql: {result.stderr}")
            sys.exit(1)
        print("✅ Schema applied successfully")
    except FileNotFoundError:
        print("❌ psql command not found. Please install PostgreSQL client tools.")
        sys.exit(1)

def run_setup_data():
    """Run the data setup script."""
    print("📊 Populating database with sample data...")
    setup_data_path = os.path.join(os.path.dirname(__file__), "setup_data.py")
    
    if not os.path.exists(setup_data_path):
        print(f"❌ Setup data file not found: {setup_data_path}")
        sys.exit(1)
    
    try:
        result = subprocess.run([sys.executable, setup_data_path], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error running setup_data.py: {result.stderr}")
            sys.exit(1)
        print("✅ Sample data loaded successfully")
    except Exception as e:
        print(f"❌ Error running setup_data.py: {e}")
        sys.exit(1)

def verify_database():
    """Verify that the database was created correctly."""
    print("🔍 Verifying database setup...")
    
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # Check if tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        expected_tables = [
            'utente', 'insegnanti', 'studenti', 'dipartimento', 'facolta',
            'corso_di_laurea', 'corso', 'edizionecorso', 'corsi_seguiti',
            'materiale_didattico', 'valutazione', 'review', 'piattaforme', 'tesi'
        ]
        
        print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check for missing tables
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
        else:
            print("✅ All expected tables present")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        sys.exit(1)

def main():
    """Main execution function."""
    print("🚀 Starting FAQBuddy Database Reset")
    print("=" * 50)
    
    check_environment()
    drop_and_create_db()
    run_schema_sql()
    run_setup_data()
    verify_database()
    
    print("=" * 50)
    print("🎉 Database reset completed successfully!")
    print(f"📊 Database: {DB_NAME}")
    print(f"🔗 Host: {DB_HOST}:{DB_PORT}")
    print("💡 You can now run the Pinecone indexing script to update your vector database.")

if __name__ == "__main__":
    main() 