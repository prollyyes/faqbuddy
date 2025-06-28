# TODO:
- migliorare prestazinoi per T2SQL ( Assolutamente da migliorare le prestazioni, non sono male dopo la prima domanda)
- migliorare la struttura del backend
- llm genera una query, eseguo la query, i dati che mi vengono buttati fuori voglio che passino un'altra volta dentro un llm in modo da avere una risposta in linguaggio naturale (text2SQL2text in pratica, llm post-processor). volendo si può fare un ibrido, se la risposta è basica uso dei template se è articolata fallback su un llm. Decidere quale è meglio. Oppure posso usare delle Naturale Language Generation (non llm) librerie per linguaggi naturali (da approfondire ma fa cagare a primo acchitto)
- ***Soluzione MIgliore Ibrido: template base + llm***
per ora ho implementato solamente llm ma ottengo un aumento del tempo di risposta abbastanza impegnativo
- Ho aggiunto un Fallback sul RAG se la risposta del T2SQL non da risultati. Sto aumentando troppo il tempo di attesa della domanda e questa cosa mi fa abbastanza incazzare.

# How to run 
- esportare il PYTHONPATH dentro /Users/.../faqbuddy/backend/src
- aggiungere le dipendenze necessarie al requirements.txt se ne manca qualcuna
```sh
uvicorn main:app --reload
```
poi runnate il frontend e provate con qualche domanda
