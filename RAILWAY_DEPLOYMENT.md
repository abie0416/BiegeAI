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