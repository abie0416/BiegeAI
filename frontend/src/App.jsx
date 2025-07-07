import React, { useState, useEffect, useRef } from "react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typingDots, setTypingDots] = useState("");
  const [debugInfo, setDebugInfo] = useState({});
  const [sessionId, setSessionId] = useState(null);
  const [conversationStats, setConversationStats] = useState({});
  const [rebuildResult, setRebuildResult] = useState(null);
  const [rebuildLoading, setRebuildLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Determine backend URL based on environment
  const isDevelopment = import.meta.env.MODE === 'development';
  const backendUrl = import.meta.env.VITE_BACKEND_URL || (isDevelopment ? "http://localhost:8000" : "https://biegeai.up.railway.app");
  const backendUrlStatus = import.meta.env.VITE_BACKEND_URL
    ? `✅ Using VITE_BACKEND_URL: ${import.meta.env.VITE_BACKEND_URL}`
    : isDevelopment 
      ? `✅ Development mode: Using localhost:8000`
      : `⚠️ VITE_BACKEND_URL not set! Using production fallback: https://biegeai.up.railway.app`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setTypingDots(prev => prev.length >= 3 ? "" : prev + ".");
      }, 500);
      return () => clearInterval(interval);
    } else {
      setTypingDots("");
    }
  }, [loading]);

  // Debug function to log information
  const logDebug = (message, data = null) => {
    const timestamp = new Date().toISOString();
    const debugMessage = `[${timestamp}] ${message}`;
    console.log(debugMessage, data);
    setDebugInfo(prev => ({
      ...prev,
      lastLog: { message: debugMessage, data, timestamp }
    }));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);
    setInput("");
    try {
      if (!backendUrl) {
        const errorMsg = "❌ VITE_BACKEND_URL is not set. Please configure it in Railway frontend service variables.";
        logDebug(errorMsg);
        setMessages((msgs) => [...msgs, { sender: "agent", text: errorMsg }]);
        setLoading(false);
        return;
      }
      logDebug("🔗 Attempting to connect to backend", { backendUrl, question: input, sessionId });
      const requestBody = { 
        question: input,
        session_id: sessionId  // Include session ID for conversation continuity
      };
      logDebug("📤 Sending request", { url: `${backendUrl}/ask`, method: "POST", body: requestBody });
      const res = await fetch(backendUrl + "/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });
      logDebug("📥 Received response", { status: res.status, statusText: res.statusText, headers: Object.fromEntries(res.headers.entries()) });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      logDebug("✅ Response data received", { answerLength: data.answer?.length, hasDebug: !!data.debug, debugInfo: data.debug });
      
      // Update session ID if provided
      if (data.session_id) {
        setSessionId(data.session_id);
        logDebug("🆔 Session ID updated", { sessionId: data.session_id });
      }
      
      setMessages((msgs) => [...msgs, { sender: "agent", text: data.answer }]);
      
      // Update conversation stats
      if (data.debug?.conversation_stats) {
        setConversationStats(data.debug.conversation_stats);
        logDebug("📊 Conversation stats updated", data.debug.conversation_stats);
      }
      
      if (data.debug) {
        logDebug("🔍 Backend debug info", data.debug);
      }
    } catch (e) {
      const errorMsg = `❌ Error: ${e.message}`;
      logDebug("❌ Request failed", { error: e.message, errorType: e.name, stack: e.stack });
      setMessages((msgs) => [...msgs, { sender: "agent", text: errorMsg }]);
    }
    setLoading(false);
  };

  // Debug function to test backend connection
  const testBackendConnection = async () => {
    if (!backendUrl) {
      logDebug("❌ VITE_BACKEND_URL is not set. Cannot test backend connection.");
      return null;
    }
    logDebug("🧪 Testing backend connection", { backendUrl });
    try {
      const res = await fetch(backendUrl + "/health");
      const data = await res.json();
      logDebug("✅ Backend health check successful", data);
      return data;
    } catch (e) {
      logDebug("❌ Backend health check failed", { error: e.message });
      return null;
    }
  };

  // Get conversation stats
  const getConversationStats = async () => {
    if (!backendUrl) return;
    try {
      const res = await fetch(backendUrl + "/conversation-stats");
      const data = await res.json();
      setConversationStats(data);
      logDebug("📊 Conversation stats loaded", data);
    } catch (e) {
      logDebug("❌ Failed to load conversation stats", { error: e.message });
    }
  };

  // Rebuild RAG knowledge base
  const rebuildRag = async () => {
    if (!backendUrl) {
      logDebug("❌ VITE_BACKEND_URL is not set. Cannot rebuild RAG.");
      return;
    }
    
    setRebuildLoading(true);
    setRebuildResult(null);
    logDebug("🔨 Starting RAG rebuild", { backendUrl });
    
    try {
      const res = await fetch(backendUrl + "/rebuild-rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      const data = await res.json();
      setRebuildResult(data);
      
      if (data.success) {
        logDebug("✅ RAG rebuild successful", data);
      } else {
        logDebug("❌ RAG rebuild failed", data);
      }
    } catch (e) {
      const errorData = {
        success: false,
        message: `Network error: ${e.message}`,
        documents_embedded: 0,
        total_sample_documents: "unknown",
        error: e.message
      };
      setRebuildResult(errorData);
      logDebug("❌ RAG rebuild network error", { error: e.message });
    } finally {
      setRebuildLoading(false);
    }
  };



  // Test connection on component mount
  useEffect(() => {
    logDebug("🚀 Frontend initialized", {
      backendUrl: backendUrl || "(not set)",
      environment: import.meta.env.MODE,
      timestamp: new Date().toISOString()
    });
    testBackendConnection();
    getConversationStats();
  }, []);

  return (
    <div style={{ 
      maxWidth: 800, 
      margin: "20px auto", 
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      height: "100vh",
      display: "flex",
      flexDirection: "column"
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color: "white",
        padding: "20px",
        borderRadius: "12px 12px 0 0",
        textAlign: "center",
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
      }}>
        <h1 style={{ margin: 0, fontSize: "2.5rem", fontWeight: "bold" }}>Biege AI</h1>
        <p style={{ margin: "8px 0 0 0", opacity: 0.9, fontSize: "1.1rem" }}>
          Your Intelligent AI Assistant
        </p>
        {/* Debug Info Display */}
        <div style={{ 
          marginTop: "10px", 
          fontSize: "0.8rem", 
          opacity: 0.8,
          textAlign: "left",
          background: "rgba(255,255,255,0.1)",
          padding: "8px",
          borderRadius: "4px"
        }}>
          <div>{backendUrlStatus}</div>
          <div>🌍 Environment: {import.meta.env.MODE}</div>
          {sessionId && (
            <div>🆔 Session: {sessionId}</div>
          )}
          {conversationStats.total_sessions !== undefined && (
            <div>💬 Sessions: {conversationStats.total_sessions}</div>
          )}
          {debugInfo.lastLog && (
            <div>📝 Last Log: {debugInfo.lastLog.message}</div>
          )}
        </div>
      </div>

      {/* Chat Container */}
      <div style={{
        flex: 1,
        background: "#f8f9fa",
        border: "1px solid #e9ecef",
        borderRadius: "0 0 12px 12px",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}>
        {/* Messages Area */}
        <div style={{
          flex: 1,
          padding: "20px",
          overflowY: "auto",
          background: "linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%)"
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: "flex",
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
              margin: "12px 0"
            }}>
              <div style={{
                maxWidth: "70%",
                padding: "12px 16px",
                borderRadius: msg.sender === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                background: msg.sender === "user" 
                  ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" 
                  : "#ffffff",
                color: msg.sender === "user" ? "white" : "#333",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                border: msg.sender === "user" ? "none" : "1px solid #e9ecef",
                wordWrap: "break-word"
              }}>
                {msg.text}
              </div>
            </div>
          ))}
          
          {/* Typing Indicator */}
          {loading && (
            <div style={{
              display: "flex",
              justifyContent: "flex-start",
              margin: "12px 0"
            }}>
              <div style={{
                padding: "12px 16px",
                borderRadius: "18px 18px 18px 4px",
                background: "#ffffff",
                border: "1px solid #e9ecef",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <div style={{
                  display: "flex",
                  gap: "4px"
                }}>
                  <div style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: "#667eea",
                    animation: "bounce 1.4s infinite ease-in-out"
                  }}></div>
                  <div style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: "#667eea",
                    animation: "bounce 1.4s infinite ease-in-out 0.2s"
                  }}></div>
                  <div style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: "#667eea",
                    animation: "bounce 1.4s infinite ease-in-out 0.4s"
                  }}></div>
                </div>
                <span style={{ color: "#666", fontSize: "0.9rem" }}>
                  Biege AI is thinking{typingDots}
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: "20px",
          background: "#ffffff",
          borderTop: "1px solid #e9ecef",
          borderRadius: "0 0 12px 12px"
        }}>
          <div style={{ display: "flex", gap: "12px" }}>
            <input
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: "25px",
                border: "2px solid #e9ecef",
                fontSize: "1rem",
                outline: "none",
                transition: "border-color 0.3s ease",
                background: "#f8f9fa"
              }}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) sendMessage(); }}
              placeholder="Ask Biege AI anything..."
              disabled={loading}
              onFocus={(e) => e.target.style.borderColor = "#667eea"}
              onBlur={(e) => e.target.style.borderColor = "#e9ecef"}
            />
            <button 
              onClick={sendMessage} 
              disabled={loading || !input.trim()} 
              style={{
                padding: "12px 24px",
                borderRadius: "25px",
                border: "none",
                background: loading || !input.trim() 
                  ? "#cccccc" 
                  : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color: "white",
                fontSize: "1rem",
                fontWeight: "600",
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
              }}
              onMouseEnter={(e) => {
                if (!loading && input.trim()) {
                  e.target.style.transform = "translateY(-2px)";
                  e.target.style.boxShadow = "0 4px 12px rgba(0,0,0,0.2)";
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = "translateY(0)";
                e.target.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
              }}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
          
          {/* Debug Buttons */}
          <div style={{ marginTop: "10px", textAlign: "center", display: "flex", gap: "8px", justifyContent: "center", flexWrap: "wrap" }}>
            <button 
              onClick={testBackendConnection}
              style={{
                padding: "8px 16px",
                borderRadius: "15px",
                border: "1px solid #667eea",
                background: "transparent",
                color: "#667eea",
                fontSize: "0.8rem",
                cursor: "pointer"
              }}
            >
              🔍 Test Connection
            </button>
            <button 
              onClick={getConversationStats}
              style={{
                padding: "8px 16px",
                borderRadius: "15px",
                border: "1px solid #667eea",
                background: "transparent",
                color: "#667eea",
                fontSize: "0.8rem",
                cursor: "pointer"
              }}
            >
              📊 Refresh Stats
            </button>
            <button 
              onClick={rebuildRag}
              disabled={rebuildLoading}
              style={{
                padding: "8px 16px",
                borderRadius: "15px",
                border: "1px solid #667eea",
                background: rebuildLoading ? "#cccccc" : "transparent",
                color: rebuildLoading ? "#999999" : "#667eea",
                fontSize: "0.8rem",
                cursor: rebuildLoading ? "not-allowed" : "pointer"
              }}
            >
              {rebuildLoading ? "🔨 Rebuilding..." : "🔨 Rebuild GraphRAG"}
            </button>

          </div>
          
          {/* Rebuild Result Display */}
          {rebuildResult && (
            <div style={{ 
              marginTop: "10px", 
              padding: "12px", 
              borderRadius: "8px", 
              background: rebuildResult.success ? "#d4edda" : "#f8d7da",
              border: `1px solid ${rebuildResult.success ? "#c3e6cb" : "#f5c6cb"}`,
              color: rebuildResult.success ? "#155724" : "#721c24",
              fontSize: "0.85rem"
            }}>
              <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
                {rebuildResult.success ? "✅ RAG Rebuild Complete" : "❌ RAG Rebuild Failed"}
              </div>
              <div>{rebuildResult.message}</div>
              {rebuildResult.documents_embedded !== undefined && (
                <div style={{ marginTop: "4px" }}>
                  📄 Total Documents: {rebuildResult.documents_embedded} / {rebuildResult.total_sample_documents}
                </div>
              )}
              {rebuildResult.details && (
                <div style={{ marginTop: "4px", fontSize: "0.8rem", opacity: 0.8 }}>
                  {rebuildResult.details}
                </div>
              )}


              {rebuildResult.error && (
                <div style={{ marginTop: "4px", fontSize: "0.8rem", opacity: 0.8 }}>
                  Error: {rebuildResult.error}
                </div>
              )}
            </div>
          )}
          

        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}

export default App; 