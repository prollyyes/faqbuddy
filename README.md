## pre-pre-handout

Come runnare per provare:

intanto create un venv (o conda usate quello che volete):
```sh
python3.9 -m venv venv
source venv/bin/activate
cd temp_backend
pip install -r requirements.txt
```

Vi servirà anche l'llm gemma:4B (nel mio caso) quindi pullate il modello su ollama (non mi ricordo i passaggi)

run some test to see if everything works:
```sh
cd temp_backend
python test_ml
```

se volete testare la ui runnate:
```sh
cd temp_backend
uvicorn api_chatbot:app
```

su un altro terminale:
```sh
cd temp_frontend
npm i && npm run dev
```
