# FAQBuddy Fresh Environment Setup

This guide explains how to completely reset your FAQBuddy environment with the updated schema and fresh Pinecone data while preserving your existing document chunks.

## 🎯 Overview

The setup process will:
1. **Reset your PostgreSQL database** with the updated schema
2. **Populate it with fresh sample data**
3. **Update Pinecone** with new database chunks
4. **Preserve existing document chunks** in Pinecone

## 📋 Prerequisites

Before running the setup, ensure you have:

- ✅ PostgreSQL server running
- ✅ Pinecone API key configured
- ✅ Python environment with all dependencies installed
- ✅ `.env` file with database and Pinecone credentials

### Required Environment Variables

Your `.env` file should contain:

```env
# Database Configuration
DB_NAME=faqbuddy
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
```

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the master setup script:

```bash
python setup_fresh_environment.py
```

This script will:
- Check all prerequisites
- Reset the database
- Update Pinecone
- Verify the setup

### Option 2: Manual Setup

If you prefer to run steps individually:

#### Step 1: Reset Database
```bash
python db/reset_database.py
```

#### Step 2: Update Pinecone
```bash
python backend/src/rag/update_pinecone_db.py
```

## 📊 What Gets Updated

### Database Changes
- **Complete reset** of your PostgreSQL database
- **Updated schema** applied from `db/schema.sql`
- **Fresh sample data** loaded from `db/setup_data.py`
- **All existing data** will be lost (this is intentional)

### Pinecone Changes
- **Database chunks** uploaded to namespace `"db"`
- **Document chunks** preserved in namespace `"documents"`
- **Enhanced chunks** preserved in namespace `"v9"` (if any)

## 🔧 Namespace Structure

After setup, your Pinecone index will have:

| Namespace | Content | Status |
|-----------|---------|--------|
| `"db"` | Database chunks (courses, professors, etc.) | **Fresh** |
| `"documents"` | PDF/document chunks | **Preserved** |
| `"v9"` | Enhanced chunks (if any) | **Preserved** |

## 📝 Database Schema

The updated schema includes:

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

### Academic Data
- `corsi_seguiti` - Course enrollments
- `materiale_didattico` - Teaching materials
- `valutazione` - Material ratings
- `review` - Course reviews
- `tesi` - Theses
- `piattaforme` - Platforms

## 🔍 Verification

After setup, you can verify everything worked:

### Check Database
```bash
python -c "
import sys
sys.path.append('backend/src')
from text_2_SQL.db_utils import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM utente')
print(f'Users: {cur.fetchone()[0]}')
cur.close()
conn.close()
"
```

### Check Pinecone
```bash
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone
load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('exams-index-enhanced')
stats = index.describe_index_stats()
for ns, ns_stats in stats.namespaces.items():
    print(f'{ns}: {ns_stats.vector_count} vectors')
"
```

### Test RAG System
```bash
python backend/src/rag/run_rag_cli.py
```

## 🛠️ Troubleshooting

### Common Issues

#### Database Connection Failed
- Check if PostgreSQL is running
- Verify database credentials in `.env`
- Ensure database user has proper permissions

#### Pinecone API Error
- Verify `PINECONE_API_KEY` in `.env`
- Check if index name exists in your Pinecone account
- Ensure you have sufficient quota

#### Missing Dependencies
```bash
pip install -r backend/requirements.txt
```

#### Permission Errors
- Ensure you have write permissions to the database
- Check file permissions for scripts

### Recovery

If something goes wrong:

1. **Database issues**: Run `python db/reset_database.py` again
2. **Pinecone issues**: Run `python backend/src/rag/update_pinecone_db.py` again
3. **Complete reset**: Run `python setup_fresh_environment.py` again

## 📈 Next Steps

After successful setup:

1. **Test the RAG system** with sample queries
2. **Add your own data** to the database
3. **Customize the chunking logic** if needed
4. **Integrate with your application**

## 🔒 Privacy Notes

The setup includes privacy protections:
- Student information is anonymized in chunks
- Professor information is preserved (public data)
- No sensitive personal data is exposed in RAG responses

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Ensure all prerequisites are met
4. Verify your `.env` configuration

---

**Happy RAGging! 🎉** 