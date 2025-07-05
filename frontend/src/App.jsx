import React, { useState, useEffect, useRef } from "react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typingDots, setTypingDots] = useState("");
  const messagesEndRef = useRef(null);

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

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);
    setInput("");
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(backendUrl + "/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      });
      const data = await res.json();
      setMessages((msgs) => [...msgs, { sender: "agent", text: data.answer }]);
    } catch (e) {
      setMessages((msgs) => [...msgs, { sender: "agent", text: "Error: " + e.message }]);
    }
    setLoading(false);
  };

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