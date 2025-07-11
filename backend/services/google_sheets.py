"""
Google Sheets service for managing RAG documents
"""
import os
import logging
from typing import List, Dict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Get logger for this module
logger = logging.getLogger(__name__)

# Google Sheets API configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
RANGE_NAME = 'Documents!A:A'  # Only column A for content

class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.spreadsheet_id = SPREADSHEET_ID
        
    def authenticate(self):
        """Authenticate with Google Sheets API using service account from environment variable"""
        try:
            # Get service account JSON from environment variable
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            
            if not service_account_json:
                logger.error("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
                return False
            
            # Parse the JSON string
            try:
                service_account_info = json.loads(service_account_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                return False
                
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets API authenticated successfully with service account from environment")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False
        
    def get_documents(self) -> List[Dict]:
        """Fetch documents from Google Sheets"""
        if not self.service:
            if not self.authenticate():
                logger.error("❌ Failed to authenticate with Google Sheets API")
                return []
        
        if not self.service:
            logger.error("❌ Service not available after authentication")
            return []
            
        if not self.spreadsheet_id:
            logger.error("❌ GOOGLE_SHEETS_SPREADSHEET_ID not configured")
            return []
            
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=RANGE_NAME
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("⚠️ No data found in Google Sheets")
                return []
                
            # Skip header row if it exists
            start_row = 1 if values[0][0].lower() in ['content', 'text', 'document'] else 0
            
            documents = []
            for i, row in enumerate(values[start_row:], start=start_row + 1):
                if len(row) >= 1 and row[0].strip():  # At least content is required and not empty
                    doc = {
                        'content': row[0].strip()
                    }
                    documents.append(doc)
                    
            logger.info(f"✅ Fetched {len(documents)} documents from Google Sheets")
            return documents
            
        except HttpError as error:
            logger.error(f"❌ Google Sheets API error: {error}")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching documents: {e}")
            return []
    
    def add_document(self, content: str) -> bool:
        """Add a new document to Google Sheets"""
        if not self.service:
            if not self.authenticate():
                logger.error("❌ Failed to authenticate with Google Sheets API")
                return False
        
        if not self.service:
            logger.error("❌ Service not available after authentication")
            return False
            
        if not self.spreadsheet_id:
            logger.error("❌ GOOGLE_SHEETS_SPREADSHEET_ID not configured")
            return False
            
        try:
            values = [[content]]
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=RANGE_NAME,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Document added successfully: {result.get('updates').get('updatedRows')} rows updated")
            return True
            
        except HttpError as error:
            logger.error(f"❌ Google Sheets API error: {error}")
            return False
        except Exception as e:
            logger.error(f"❌ Error adding document: {e}")
            return False
    


# Global instance
sheets_service = GoogleSheetsService() 