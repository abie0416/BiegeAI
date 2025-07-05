# Biege AI 🤖

Your Intelligent AI Assistant powered by advanced RAG (Retrieval-Augmented Generation) and MCP (Multi-Component Pipeline) technology.

## 🚀 Features

- **RAG System**: Retrieves relevant information from your knowledge base
- **MCP Pipeline**: Multi-component reasoning with multiple tools
- **Gemini Integration**: Powered by Google's latest Gemini model
- **ChromaDB**: Vector database for semantic search
- **Modern UI**: Beautiful React chat interface
- **Real-time Chat**: Dynamic typing indicators and smooth interactions

## 🏗️ Architecture

```
Frontend (React) ←→ Backend (FastAPI) ←→ ChromaDB + Gemini API
```

- **Frontend**: React with Vite, modern chat UI
- **Backend**: FastAPI with LangChain integration
- **Database**: ChromaDB for vector storage
- **AI Model**: Google Gemini Pro

## 🛠️ Tech Stack

- **Frontend**: React, Vite, CSS-in-JS
- **Backend**: FastAPI, Python 3.10+
- **AI/ML**: LangChain, ChromaDB, Google Gemini
- **Deployment**: Railway

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Add your Gemini API key to .env file
python init_knowledge_base.py
python -m uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Deployment

### Railway Deployment

1. **Fork/Clone** this repository
2. **Connect to Railway**:
   - Go to [Railway.app](https://railway.app)
   - Create new project
   - Connect your GitHub repository

3. **Deploy Backend**:
   - Add service → GitHub Repo → Select backend folder
   - Add environment variable: `GEMINI_API_KEY=your_key_here`

4. **Deploy Frontend**:
   - Add service → GitHub Repo → Select frontend folder
   - Update frontend API URL to point to backend

5. **Get your URLs**:
   - Backend: `https://your-backend.railway.app`
   - Frontend: `https://your-frontend.railway.app`

## 🔧 Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Customizing Knowledge Base
Edit `backend/init_knowledge_base.py` to add your own documents:
```python
sample_documents = [
    "Your custom document here...",
    "Another document...",
]
```

## 📚 API Endpoints

- `POST /ask` - Chat with the AI agent
- `GET /health` - Health check

## 🎨 UI Features

- **Modern Design**: Gradient themes and smooth animations
- **Dynamic Typing**: Animated typing indicators
- **Responsive**: Works on all devices
- **Auto-scroll**: Automatically scrolls to latest messages
- **Error Handling**: Graceful error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use this project for your own AI assistant!

## 🆘 Support

If you encounter any issues:
1. Check the debug logs in your terminal
2. Verify your Gemini API key is valid
3. Ensure all dependencies are installed
4. Check Railway deployment logs

---

**Built with ❤️ using FastAPI, React, and LangChain** 