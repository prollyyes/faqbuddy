#!/usr/bin/env python3
"""
Docker-based Database Setup for FAQBuddy
This script sets up a fresh PostgreSQL database using Docker and updates Pinecone.
"""

import os
import sys
import subprocess
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Docker configuration
DOCKER_CONTAINER_NAME = "faqbuddy_postgres_db"
DOCKER_PORT = "5433"
DB_NAME = "faqbuddy_db"
DB_USER = "db_user"
DB_PASSWORD = "pwd"
DB_HOST = "localhost"
DB_PORT = DOCKER_PORT

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step_num, total_steps, description):
    """Print a formatted step."""
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")
    print("-" * 40)

def check_docker():
    """Check if Docker is available."""
    print_step(1, 6, "Checking Docker")
    
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker not found or not working")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False

def stop_existing_container():
    """Stop and remove existing container if it exists."""
    print_step(2, 6, "Stopping Existing Container")
    
    try:
        # Check if container exists
        result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={DOCKER_CONTAINER_NAME}"], 
                              capture_output=True, text=True)
        
        if DOCKER_CONTAINER_NAME in result.stdout:
            print(f"🔍 Found existing container: {DOCKER_CONTAINER_NAME}")
            
            # Stop container if running
            stop_result = subprocess.run(["docker", "stop", DOCKER_CONTAINER_NAME], 
                                       capture_output=True, text=True)
            if stop_result.returncode == 0:
                print(f"✅ Stopped existing container: {DOCKER_CONTAINER_NAME}")
            else:
                print(f"ℹ️  Container was not running: {DOCKER_CONTAINER_NAME}")
            
            # Remove container
            rm_result = subprocess.run(["docker", "rm", DOCKER_CONTAINER_NAME], 
                                     capture_output=True, text=True)
            if rm_result.returncode == 0:
                print(f"✅ Removed existing container: {DOCKER_CONTAINER_NAME}")
            else:
                print(f"ℹ️  Container was already removed: {DOCKER_CONTAINER_NAME}")
        else:
            print(f"ℹ️  No existing container found: {DOCKER_CONTAINER_NAME}")
        
        # Return True to indicate success (whether container existed or not)
        return True
            
    except Exception as e:
        print(f"⚠️  Warning: Could not check for existing container: {e}")
        print("Continuing anyway...")
        # Return True even if there's an error, as this is not critical
        return True

def start_database():
    """Start the PostgreSQL database using Docker Compose."""
    print_step(3, 6, "Starting Database")
    
    try:
        print("🐳 Starting PostgreSQL with Docker Compose...")
        
        # Try docker-compose first
        try:
            result = subprocess.run(["docker-compose", "up", "-d"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Docker Compose started successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ Docker Compose failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("ℹ️  docker-compose not found. Trying docker compose (newer version)...")
            try:
                result = subprocess.run(["docker", "compose", "up", "-d"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Docker Compose started successfully")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"❌ Docker Compose failed: {result.stderr}")
                    return False
            except FileNotFoundError:
                print("❌ Neither 'docker-compose' nor 'docker compose' found")
                print("Please install Docker Compose")
                return False
        
        # Wait for database to be ready
        print("⏳ Waiting for database to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                result = subprocess.run([
                    "docker", "exec", DOCKER_CONTAINER_NAME,
                    "pg_isready", "-U", DB_USER, "-d", DB_NAME
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Database is ready!")
                    return True
                else:
                    print(f"⏳ Database not ready yet... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"⏳ Waiting for container... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
        
        print("❌ Database failed to start within expected time")
        return False
        
    except Exception as e:
        print(f"❌ Error starting database: {e}")
        return False

def apply_schema():
    """Apply the schema.sql file to the database."""
    print_step(4, 8, "Applying Schema")
    
    try:
        # Read the schema file
        schema_file_path = os.path.join(os.path.dirname(__file__), "db", "schema_clean.sql")
        
        if not os.path.exists(schema_file_path):
            print(f"❌ Schema file not found: {schema_file_path}")
            return False
        
        with open(schema_file_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Connect to database and apply schema
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute the schema
        cursor.execute(schema_sql)
        
        cursor.close()
        conn.close()
        
        print("✅ Schema applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False

def verify_database():
    """Verify that the database was created correctly."""
    print_step(5, 8, "Verifying Database")
    
    try:
        # Test connection using psql
        result = subprocess.run([
            "docker", "exec", DOCKER_CONTAINER_NAME,
            "psql", "-U", DB_USER, "-d", DB_NAME, "-c",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database connection successful")
            print("📋 Tables found:")
            lines = result.stdout.strip().split('\n')
            for line in lines[2:-1]:  # Skip header and footer
                if line.strip():
                    print(f"   - {line.strip()}")
        else:
            print(f"❌ Database verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    
    return True

def populate_sample_data():
    """Populate the database with sample data."""
    print_step(6, 8, "Populating Sample Data")
    
    try:
        script_path = "db/setup_data_docker.py"
        print(f"🔄 Running data population: {script_path}")
        
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sample data populated successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Data population failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running data population: {e}")
        return False
    
    return True

def update_environment_file():
    """Update .env file with Docker database settings."""
    print_step(7, 8, "Updating Environment")
    
    env_content = f"""# Database Configuration (Docker)
DB_NAME={DB_NAME}
DB_USER={DB_USER}
DB_PASSWORD={DB_PASSWORD}
DB_HOST={DB_HOST}
DB_PORT={DB_PORT}

# Pinecone Configuration
PINECONE_API_KEY={os.getenv('PINECONE_API_KEY', 'your_pinecone_api_key_here')}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file updated with Docker database settings")
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False
    
    return True

def update_pinecone():
    """Update Pinecone with fresh database chunks."""
    print_step(8, 8, "Updating Pinecone")
    
    try:
        script_path = "backend/src/rag/update_pinecone_db.py"
        print(f"🔄 Running Pinecone update: {script_path}")
        
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True)
        
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
    print_header("FAQBuddy Docker Database Setup")
    
    print("This script will:")
    print("1. Check Docker availability")
    print("2. Stop existing database container (if any)")
    print("3. Start fresh PostgreSQL database with Docker")
    print("4. Apply database schema")
    print("5. Verify database setup")
    print("6. Populate with sample data")
    print("7. Update environment file")
    print("8. Update Pinecone with fresh data")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Setup cancelled")
        return
    
    # Execute steps
    steps = [
        ("Checking Docker", check_docker),
        ("Stopping Existing Container", stop_existing_container),
        ("Starting Database", start_database),
        ("Applying Schema", apply_schema),
        ("Verifying Database", verify_database),
        ("Populating Sample Data", populate_sample_data),
        ("Updating Environment", update_environment_file),
        ("Updating Pinecone", update_pinecone)
    ]
    
    for i, (description, step_func) in enumerate(steps, 1):
        if not step_func():
            print(f"\n❌ Setup failed at step {i}: {description}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    print_header("Docker Database Setup Completed Successfully!")
    print("🎉 Your FAQBuddy environment has been set up with Docker!")
    print("\n📊 What was accomplished:")
    print("   ✅ Fresh PostgreSQL database in Docker")
    print("   ✅ Updated schema applied")
    print("   ✅ Sample data loaded")
    print("   ✅ Pinecone updated with database chunks")
    print("\n🔧 Database Details:")
    print(f"   - Container: {DOCKER_CONTAINER_NAME}")
    print(f"   - Host: {DB_HOST}:{DB_PORT}")
    print(f"   - Database: {DB_NAME}")
    print(f"   - User: {DB_USER}")
    print("\n💡 Next steps:")
    print("   - Test your RAG system: python backend/src/rag/run_rag_cli.py")
    print("   - Stop database: docker-compose down")
    print("   - Start database: docker-compose up -d")

if __name__ == "__main__":
    main() 