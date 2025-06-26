import os
import io
from fastapi import FastAPI, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0, browser="chrome")
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

app = FastAPI()

def get_folder_id(service, parent_name, child_name):
    # Trova la cartella FAQBuddy
    results = service.files().list(
        q=f"name='{parent_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    parent_folders = results.get('files', [])
    if not parent_folders:
        raise Exception(f"Cartella '{parent_name}' non trovata su Drive.")
    parent_id = parent_folders[0]['id']

    # Trova la sottocartella (Tesi o MaterialeDidattico)
    results = service.files().list(
        q=f"name='{child_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    child_folders = results.get('files', [])
    if not child_folders:
        raise Exception(f"Sottocartella '{child_name}' non trovata in '{parent_name}'.")
    return child_folders[0]['id']


def debug_list_folders(service):
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    print("Cartelle trovate:")
    for f in folders:
        print(f["name"])
        

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    tipo: str = Form(...)
):
    """
    file: Il file da caricare
    tipo: Il tipo di file, deve essere 'Tesi' o 'Materiale_Didattico'
    """
    service = get_service()
    debug_list_folders(service)  # Debug: Elenco delle cartelle
    if tipo not in ["Tesi", "Materiale_Didattico"]:
        return {"error": "tipo deve essere 'Tesi' o 'Materiale_Didattico'"}
    folder_id = get_folder_id(service, "FAQBuddy", tipo)
    file_metadata = {'name': file.filename, 'parents': [folder_id]}
    contents = await file.read()
    with open(file.filename, "wb") as f:
        f.write(contents)
    media = MediaFileUpload(file.filename, resumable=True)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    os.remove(file.filename)
    return {"file_id": uploaded.get('id')}


@app.get("/download")
def list_all_files():
    service = get_service()
    debug_list_folders(service)  # Debug: Elenco delle cartelle
    result = {}
    for tipo in ["Tesi", "Materiale_Didattico"]:
        try:
            folder_id = get_folder_id(service, "FAQBuddy", tipo)
            files = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields="files(id, name)"
            ).execute().get('files', [])
            result[tipo] = [{"id": f["id"], "name": f["name"]} for f in files]
        except Exception as e:
            result[tipo] = []
    return result

@app.get("/download/{file_id}")
def download_file(file_id: str):
    service = get_service()
    # Recupera il nome originale del file
    file_info = service.files().get(fileId=file_id, fields="name").execute()
    filename = file_info["name"]
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(fh, media_type="application/octet-stream", headers=headers)

# from typing import Optional

# @app.get("/create_folder/{name}")
# @app.get("/create_folder/{name}/{parent_id}")
# def create_folder_with_parent(name: str, parent_id: Optional[str] = None):
#     service = get_service()
#     file_metadata = {
#         'name': name,
#         'mimeType': 'application/vnd.google-apps.folder'
#     }
#     if parent_id:
#         file_metadata['parents'] = [parent_id]
#     folder = service.files().create(body=file_metadata, fields='id').execute()
#     return {"created_folder_id": folder.get('id')}
