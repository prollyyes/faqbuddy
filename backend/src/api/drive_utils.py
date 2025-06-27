# Handle any interaction with Google Drive

import os

def get_drive_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
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

def get_folder_id(service, parent_name, child_name):
    ###################################
    # Trova l'ID della cartella FAQBuddy per debugging purposes
    # service = get_service()
    # results = service.files().list(
    #     q="name='FAQBuddy' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    #     spaces='drive',
    #     fields="files(id, name)"
    # ).execute()
    # folders = results.get('files', [])
    # if folders:
    #     faqbuddy_id = folders[0]['id']
    #     print("ID FAQBuddy:", faqbuddy_id)
    # else:
    #     print("Cartella FAQBuddy non trovata")
    ###################################
    # Trova la cartella principale
    results = service.files().list(
        q=f"name='{parent_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    parent_folders = results.get('files', [])
    if not parent_folders:
        raise Exception(f"Cartella '{parent_name}' non trovata su Drive.")
    parent_id = parent_folders[0]['id']

    # Trova la sottocartella
    results = service.files().list(
        q=f"name='{child_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    child_folders = results.get('files', [])
    if not child_folders:
        raise Exception(f"Sottocartella '{child_name}' non trovata in '{parent_name}'.")
    return child_folders[0]['id']

def delete_drive_file(file_id):
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
    
    
def upload_file_to_drive(file_path, filename, folder_id):
    service = get_drive_service()
    from googleapiclient.http import MediaFileUpload
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded.get('id')