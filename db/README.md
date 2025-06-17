
```sh
docker run --name faqbuddy_postgres_db \
  -e POSTGRES_PASSWORD=pwd \          
  -e POSTGRES_USER=db_user \    
  -e POSTGRES_DB=faqbuddy_db \
  -p 5433:5432 \
  -d postgres:13
```

to see if everything works:
```sh
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db
```

create and populate with sample data:
```sh
psql -h localhost -p 5433 -U db_user -d faqbuddy_db -f schema.sql
psql -h localhost -p 5433 -U db_user -d faqbuddy_db -f sample_data.sql
python test_db.py
```