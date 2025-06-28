#!/usr/bin/env python3
"""
Test database connection and data
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_NAME = "faqbuddy_db"
DB_USER = "db_user"
DB_PASSWORD = "pwd"
DB_HOST = "localhost"
DB_PORT = "5433"

def test_connection():
    """Test database connection and check table data."""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        
        # Check if tables exist and have data
        tables = [
            'dipartimento', 'facolta', 'corso_di_laurea', 'corso', 
            'edizionecorso', 'materiale_didattico', 'review', 'valutazione',
            'piattaforme', 'insegnanti', 'tesi'
        ]
        
        print("🔍 Checking database tables and data:")
        print("-" * 50)
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} rows")
            except Exception as e:
                print(f"❌ {table}: Error - {e}")
        
        cursor.close()
        conn.close()
        
        print("-" * 50)
        print("✅ Database connection test completed")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection() 