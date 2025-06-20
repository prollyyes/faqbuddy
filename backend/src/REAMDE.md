# TODO:
- Fare benchmark per T2SQL ( Assolutamente da migliorare le prestazioni, non sono male dopo la prima domanda)
- integrazione switcher -> T2SQL + RAG. Ho eseguito Test sulla pipeline intera e non è male
- migliorare la struttura del backend
- llm genera una query, eseguo la query, i dati che mi vengono buttati fuori voglio che passino un'altra volta dentro un llm in modo da avere una risposta in linguaggio naturale (text2SQL2text in pratica, llm post-processor). volendo si può fare un ibrido, se la risposta è basica uso dei template se è articolata fallback su un llm. Decidere quale è meglio. Oppure posso usare delle Naturale Language Generation (non llm) librerie per linguaggi naturali (da approfondire ma fa cagare a primo acchitto)
- ***Soluzione MIgliore Ibrido: template base + llm***



# How to run 
- esportare il PYTHONPATH dentro /Users/.../faqbuddy/backend
- aggiungere le dipendenze necessarie al requirements.txt se ne manca qualcuna
```sh
uvicorn text_2_SQL.Text2SQL:app --reload
```
poi runnate il frontend e provate con qualche domanda
