# Railway Deployment Guide

This is a monorepo containing both backend (FastAPI) and frontend (React) applications.

## Deployment Instructions

### Option 1: Deploy as Separate Services (Recommended)

1. **Create a new Railway project**
2. **Connect your GitHub repository**: `abie0416/BiegeAI`
3. **Railway will detect both services automatically**
4. **Deploy both services separately**:
   - **Backend Service**: Root directory = `backend`
   - **Frontend Service**: Root directory = `frontend`

### Option 2: Manual Service Creation

If Railway doesn't auto-detect the services:

1. **Create Backend Service**:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Create Frontend Service**:
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Start Command: `npx serve -s dist -l $PORT`

### Environment Variables

**Backend Service**:
- `GEMINI_API_KEY`: Your Gemini API key

**Frontend Service**:
- `VITE_BACKEND_URL`: URL of your backend service (e.g., `https://your-backend-service.railway.app`)

### Important Notes

- **Do NOT deploy from the root directory** - this will fail
- **Each service must have its own root directory** (`backend/` or `frontend/`)
- **Railway will automatically set the `$PORT` environment variable**

### Troubleshooting

If you get "Nixpacks was unable to generate a build plan":
1. Make sure you're deploying from the correct subdirectory
2. Check that the root directory is set to `backend` or `frontend`
3. Verify that `requirements.txt` (backend) or `package.json` (frontend) exists

## Google Sheets Service Account Setup

This application uses Google Sheets for document storage. To deploy to Railway, you need to set up the service account credentials as environment variables.

### 1. Get Your Service Account JSON

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Find your service account or create a new one
4. Download the JSON key file

### 2. Set Up Railway Environment Variables

In your Railway project dashboard:

1. Go to your project → Variables
2. Add the following environment variables:

#### Required Variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Your Google Sheets spreadsheet ID
- `GOOGLE_SERVICE_ACCOUNT_JSON`: The entire contents of your service account JSON file

#### Optional Variables:
- `PORT`: Railway will set this automatically
- `RAILWAY_ENVIRONMENT`: Railway will set this automatically

### 3. Setting GOOGLE_SERVICE_ACCOUNT_JSON

1. Open your downloaded service account JSON file in a text editor
2. Copy the entire contents (including all the curly braces and quotes)
3. In Railway, create a new variable:
   - **Key:** `GOOGLE_SERVICE_ACCOUNT_JSON`
   - **Value:** Paste the entire JSON content

**Important:** The JSON should be on a single line or properly formatted. Railway will handle the formatting.

### 4. Share Your Google Sheet

1. Open your Google Sheets document
2. Click "Share" in the top right
3. Add your service account email (found in the JSON file under `client_email`)
4. Give it "Editor" permissions

### 5. Deploy

Once all environment variables are set, deploy your application. The service will:

1. Automatically initialize the RAG knowledge base on startup
2. Fetch documents from Google Sheets
3. Build the advanced RAG index with AI metadata
4. Be ready to handle queries immediately

### Troubleshooting

- **"GOOGLE_SERVICE_ACCOUNT_JSON not set"**: Make sure you've added the environment variable in Railway
- **"Invalid JSON"**: Check that the entire JSON content was copied correctly
- **"Permission denied"**: Ensure the service account email has access to the Google Sheet
- **"Spreadsheet not found"**: Verify the `GOOGLE_SHEETS_SPREADSHEET_ID` is correct

### Local Development

For local development, you can still use the `google_sheets_service_account.json` file. The code will automatically use the environment variable if available, or fall back to the file if it exists. 