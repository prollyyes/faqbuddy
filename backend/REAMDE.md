# TODO:
- Fare benchmark per T2SQL ( Assolutamente da migliorare le prestazioni)
- integrazione switcher -> T2SQL + RAG
- migliorare la struttura del backend



# How to run 
- esportare il PYTHONPATH dentro /Users/.../faqbuddy/backend
- aggiungere le dipendenze necessarie al requirements.txt se ne manca qualcuna
```sh
uvicorn text_2_SQL.Text2SQL:app --reload
```
poi runnate il frontend e provate con qualche domanda
