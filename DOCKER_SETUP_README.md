# FAQBuddy Docker Database Setup

This guide explains how to set up FAQBuddy with a containerized PostgreSQL database using Docker.

## 🎯 Overview

The Docker setup provides:
- **Isolated PostgreSQL database** in a Docker container
- **Automatic schema initialization** on first run
- **Easy cleanup and reset** capabilities
- **Consistent environment** across different machines

## 📋 Prerequisites

- ✅ **Docker** installed and running
- ✅ **Docker Compose** (or `docker compose` for newer versions)
- ✅ **Python** with required dependencies
- ✅ **Pinecone API key** configured

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the Docker setup script:

```bash
python setup_docker_database.py
```

This script will:
1. Check Docker availability
2. Stop/remove existing containers
3. Start fresh PostgreSQL database
4. Apply schema automatically
5. Populate with sample data
6. Update Pinecone with fresh chunks

### Option 2: Manual Setup

#### Step 1: Start Database Container
```bash
docker-compose up -d
```

#### Step 2: Wait for Database to be Ready
```bash
docker logs faqbuddy_postgres_db
```

#### Step 3: Populate with Sample Data
```bash
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db -c "SELECT version();"
```

#### Step 4: Run Setup Script (from host)
```bash
python db/setup_data_docker.py
```

#### Step 5: Update Pinecone
```bash
python backend/src/rag/update_pinecone_db.py
```

## 🔧 Database Configuration

### Container Details
- **Image**: PostgreSQL 13
- **Container Name**: `faqbuddy_postgres_db`
- **Port**: `5433` (mapped to container's `5432`)
- **Database**: `faqbuddy_db`
- **User**: `db_user`
- **Password**: `pwd`

### Environment Variables
The setup automatically creates/updates your `.env` file:

```env
# Database Configuration (Docker)
DB_NAME=faqbuddy_db
DB_USER=db_user
DB_PASSWORD=pwd
DB_HOST=localhost
DB_PORT=5433

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
```

## 📊 Schema Structure

The updated schema includes all necessary tables with proper relationships:

### Core Tables
- `utente` - Base user table
- `insegnanti` - Professors (inherits from utente)
- `studenti` - Students (inherits from utente)

### Academic Structure
- `dipartimento` - Departments
- `facolta` - Faculties
- `corso_di_laurea` - Degree programs
- `corso` - Individual courses
- `edizionecorso` - Course editions
- `piattaforme` - Platforms

### Academic Data
- `corsi_seguiti` - Course enrollments
- `materiale_didattico` - Teaching materials
- `valutazione` - Material ratings
- `review` - Course reviews
- `tesi` - Theses

## 🐳 Docker Commands

### Start Database
```bash
docker-compose up -d
```

### Stop Database
```bash
docker-compose down
```

### View Logs
```bash
docker logs faqbuddy_postgres_db
```

### Connect to Database
```bash
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db
```

### Reset Database (Complete Cleanup)
```bash
docker-compose down -v  # Removes volumes too
docker-compose up -d    # Fresh start
```

### Backup Database
```bash
docker exec faqbuddy_postgres_db pg_dump -U db_user faqbuddy_db > backup.sql
```

### Restore Database
```bash
docker exec -i faqbuddy_postgres_db psql -U db_user -d faqbuddy_db < backup.sql
```

## 🔍 Verification

### Check Database Status
```bash
# Check if container is running
docker ps | grep faqbuddy_postgres_db

# Check database health
docker exec faqbuddy_postgres_db pg_isready -U db_user -d faqbuddy_db
```

### Verify Tables
```bash
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db -c "
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t 
WHERE table_schema = 'public' 
ORDER BY table_name;
"
```

### Check Sample Data
```bash
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db -c "
SELECT 'Users' as table_name, COUNT(*) as count FROM utente
UNION ALL
SELECT 'Departments', COUNT(*) FROM dipartimento
UNION ALL
SELECT 'Faculties', COUNT(*) FROM facolta
UNION ALL
SELECT 'Degree Programs', COUNT(*) FROM corso_di_laurea
UNION ALL
SELECT 'Courses', COUNT(*) FROM corso;
"
```

## 🛠️ Troubleshooting

### Common Issues

#### Docker Not Running
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

#### Port Already in Use
```bash
# Check what's using port 5433
lsof -i :5433

# Or change port in docker-compose.yml
ports:
  - "5434:5432"  # Use 5434 instead
```

#### Container Won't Start
```bash
# Check logs
docker logs faqbuddy_postgres_db

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

#### Database Connection Failed
```bash
# Check if database is ready
docker exec faqbuddy_postgres_db pg_isready -U db_user -d faqbuddy_db

# Check environment variables
docker exec faqbuddy_postgres_db env | grep POSTGRES
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x setup_docker_database.py
chmod +x db/setup_data_docker.py
```

### Recovery Steps

1. **Complete Reset**:
   ```bash
   docker-compose down -v
   python setup_docker_database.py
   ```

2. **Database Only Reset**:
   ```bash
   docker-compose down
   docker-compose up -d
   python db/setup_data_docker.py
   ```

3. **Pinecone Only Reset**:
   ```bash
   python backend/src/rag/update_pinecone_db.py
   ```

## 📈 Next Steps

After successful setup:

1. **Test the RAG system**:
   ```bash
   python backend/src/rag/run_rag_cli.py
   ```

2. **Add your own data**:
   - Modify `db/setup_data_docker.py` with your data
   - Or insert directly via SQL

3. **Customize the setup**:
   - Modify `docker-compose.yml` for different ports/configurations
   - Update schema in `db/schema.sql`

4. **Production deployment**:
   - Use proper passwords and security
   - Set up backups
   - Configure monitoring

## 🔒 Security Notes

- **Default credentials** are for development only
- **Change passwords** for production use
- **Use environment variables** for sensitive data
- **Restrict network access** in production

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Docker logs: `docker logs faqbuddy_postgres_db`
3. Verify your `.env` configuration
4. Ensure Docker is running and accessible

---

**Happy Docker RAGging! 🐳🎉** 