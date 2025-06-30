#!/usr/bin/env python3
"""
Test script for Neon database connection
"""

import os
import psycopg2
from dotenv import load_dotenv

def test_neon_connection():
    """Test connection to Neon database."""
    
    # Load environment variables
    load_dotenv()
    
    # Get connection parameters
    db_params = {
        'host': os.getenv('DB_NEON_HOST', 'ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech'),
        'database': os.getenv('DB_NEON_NAME', 'neondb'),
        'user': os.getenv('DB_NEON_USER', 'neondb_owner'),
        'password': os.getenv('DB_NEON_PASSWORD', 'npg_81IXpKWZQxEa'),
        'port': os.getenv('DB_NEON_PORT', '5432')
    }
    
    print("🔍 Testing Neon Database Connection...")
    print(f"Host: {db_params['host']}")
    print(f"Database: {db_params['database']}")
    print(f"User: {db_params['user']}")
    print(f"Port: {db_params['port']}")
    print("-" * 50)
    
    try:
        # Attempt connection
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print("✅ Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Test if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n⚠️  No tables found in the database")
        
        cursor.close()
        conn.close()
        print("\n✅ Database connection test completed successfully!")
        
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_neon_connection() 