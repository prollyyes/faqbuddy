#!/usr/bin/env python3
"""
Test script to verify Docker setup
"""

import subprocess
import sys
import time

def test_docker_container():
    """Test if the Docker container is running and accessible."""
    print("🔍 Testing Docker container...")
    
    try:
        # Check if container is running
        result = subprocess.run(["docker", "ps", "--filter", "name=faqbuddy_postgres_db"], 
                              capture_output=True, text=True)
        
        if "faqbuddy_postgres_db" in result.stdout:
            print("✅ Container is running")
        else:
            print("❌ Container is not running")
            return False
        
        # Test database connection
        result = subprocess.run([
            "docker", "exec", "faqbuddy_postgres_db",
            "pg_isready", "-U", "db_user", "-d", "faqbuddy_db"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database is ready")
        else:
            print("❌ Database is not ready")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing container: {e}")
        return False

def test_database_tables():
    """Test if database tables exist and have data."""
    print("🔍 Testing database tables...")
    
    try:
        # Check tables
        result = subprocess.run([
            "docker", "exec", "faqbuddy_postgres_db",
            "psql", "-U", "db_user", "-d", "faqbuddy_db", "-c",
            "SELECT COUNT(*) FROM utente;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database tables exist and are accessible")
            print(f"   Users count: {result.stdout.strip().split('\n')[2]}")
        else:
            print("❌ Database tables not accessible")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing tables: {e}")
        return False

def test_python_connection():
    """Test Python connection to the database."""
    print("🔍 Testing Python database connection...")
    
    try:
        # Test the setup_data_docker.py script
        result = subprocess.run([sys.executable, "db/setup_data_docker.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Python can connect to database")
            print("✅ Sample data is accessible")
        else:
            print("❌ Python cannot connect to database")
            print(f"Error: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Python connection: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing FAQBuddy Docker Setup")
    print("=" * 40)
    
    tests = [
        ("Docker Container", test_docker_container),
        ("Database Tables", test_database_tables),
        ("Python Connection", test_python_connection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Docker setup is working correctly.")
        print("\n💡 Next steps:")
        print("   - Run: python setup_docker_database.py")
        print("   - Or test RAG: python backend/src/rag/run_rag_cli.py")
    else:
        print("❌ Some tests failed. Please check your Docker setup.")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure Docker is running")
        print("   - Run: docker-compose up -d")
        print("   - Check logs: docker logs faqbuddy_postgres_db")

if __name__ == "__main__":
    main() 