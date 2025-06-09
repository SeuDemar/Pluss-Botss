from google.oauth2 import service_account
from googleapiclient.discovery import build
from .config import SPREADSHEET_ID, SERVICE_ACCOUNT_FILE

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

def add_to_sheet(values):
    body = {'values': [values]}
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    print(f"{result.get('updates').get('updatedCells')} células atualizadas.")

