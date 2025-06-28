Create the Docker container using postgres image
```sh
docker run --name faqbuddy_postgres_db -e POSTGRES_PASSWORD=pwd -e POSTGRES_USER=db_user -e POSTGRES_DB=faqbuddy_db -p 5433:5432 -d postgres:13
```

create and populate with sample data:
```sh
python create_db.py local
```

> **IMPORTANTE:**  
> SE INVECE DI `local` INSERISCI `neon` DISTRUGGERAI E RICREERAI IL DB REMOTO, DA FARE SOLO SE NE SEI