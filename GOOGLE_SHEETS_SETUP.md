# Google Sheets Setup for RAG Documents

This guide explains how to set up Google Sheets integration for storing and managing RAG documents.

## 1. Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name the first sheet "Documents"
4. Add a header in row 1:
   - Column A: `Content` (the main document text)
   
**Note**: The AI model will automatically generate metadata (source, category, name, trait, game) from the content.

## 2. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

## 3. Create Service Account (Recommended for Production)

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in service account details
4. Click "Create and Continue"
5. Skip role assignment, click "Done"
6. Click on the created service account
7. Go to "Keys" tab
8. Click "Add Key" > "Create new key"
9. Choose JSON format
10. Download the JSON file
11. Rename it to `service-account-key.json`
12. Place it in the `backend/` directory

## 4. Alternative: OAuth2 Setup (for Development)

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Download the JSON file
5. Rename it to `credentials.json`
6. Place it in the `backend/` directory

## 5. Share Google Sheet

1. Open your Google Sheet
2. Click "Share" button
3. If using service account: Add the service account email (found in the JSON file)
4. If using OAuth2: Add your Google account email
5. Give "Editor" permissions

## 6. Environment Variables

Add these to your environment variables:

```bash
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

To find your spreadsheet ID:
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
- Copy the ID part

## 7. Add Sample Data

Add some sample documents to your Google Sheet (only the Content column is needed):

| Content |
|---------|
| Eric是O孝子，他非常孝顺父母，经常帮助家里做家务。Eric在朋友中很受欢迎，大家都喜欢和他一起玩。 |
| Eric投篮还可以，但是没有zzn准。Eric在篮球场上表现不错，但是zzn的投篮技术更加精准，命中率更高。 |
| 911比718牛逼，保时捷911是经典跑车，性能卓越。718虽然也不错，但在很多方面都不如911出色。 |
| 马棚是老司机，开车技术很好，经验丰富。他经常开车带大家出去玩，大家都觉得坐他的车很安全。 |

The AI will automatically analyze each document and generate appropriate metadata.

## 8. API Endpoints

Once set up, you can use this endpoint:

- `POST /rebuild-rag` - Rebuild RAG with latest documents from Google Sheets

**Note**: Document management is done directly in Google Sheets. The system fetches documents and automatically generates metadata using AI.

## 9. Testing

1. Start your backend server
2. Rebuild RAG: `POST /rebuild-rag` (or use the "🔨 Rebuild RAG" button in the frontend)
3. Ask questions to test RAG functionality

## Troubleshooting

- **Authentication errors**: Check that credentials files are in the correct location
- **Permission errors**: Ensure the Google account has edit access to the sheet
- **API quota exceeded**: Check Google Cloud Console for quota limits
- **Sheet not found**: Verify the spreadsheet ID is correct

## Security Notes

- Never commit credential files to version control
- Use service accounts for production deployments
- Regularly rotate credentials
- Monitor API usage in Google Cloud Console 