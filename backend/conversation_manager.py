import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a single message in the conversation"""
    sender: str  # "user" or "agent"
    text: str
    timestamp: float
    session_id: str

@dataclass
class ConversationSession:
    """Represents a conversation session"""
    session_id: str
    messages: List[Message]
    last_activity: float
    created_at: float

class ConversationManager:
    """Manages conversation history with session tracking and cost optimization"""
    
    def __init__(self, 
                 max_sessions: int = 100,
                 session_timeout_minutes: int = 30,
                 max_messages_per_session: int = 50,
                 max_context_length: int = 4000,
                 consecutive_timeout_minutes: int = 5):
        """
        Initialize conversation manager
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
            session_timeout_minutes: Minutes of inactivity before session expires
            max_messages_per_session: Maximum messages per session
            max_context_length: Maximum characters for context (cost optimization)
            consecutive_timeout_minutes: Minutes to consider messages as consecutive
        """
        self.max_sessions = max_sessions
        self.session_timeout_minutes = session_timeout_minutes
        self.max_messages_per_session = max_messages_per_session
        self.max_context_length = max_context_length
        self.consecutive_timeout_minutes = consecutive_timeout_minutes
        
        # In-memory storage (can be replaced with Redis/database)
        self.sessions: Dict[str, ConversationSession] = {}
        
        logger.info(f"ConversationManager initialized with max_sessions={max_sessions}, "
                   f"session_timeout={session_timeout_minutes}min, "
                   f"max_messages={max_messages_per_session}, "
                   f"max_context={max_context_length}chars")
    
    def _generate_session_id(self, user_identifier: str = "default") -> str:
        """Generate a unique session ID"""
        timestamp = int(time.time())
        return f"{user_identifier}_{timestamp}"
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to free memory"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > (self.session_timeout_minutes * 60):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.debug(f"Removed expired session: {session_id}")
        
        # If still too many sessions, remove oldest ones
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(), 
                key=lambda x: x[1].last_activity
            )
            sessions_to_remove = len(self.sessions) - self.max_sessions
            for i in range(sessions_to_remove):
                session_id = sorted_sessions[i][0]
                del self.sessions[session_id]
                logger.debug(f"Removed old session due to limit: {session_id}")
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        self._cleanup_expired_sessions()
        
        if session_id and session_id in self.sessions:
            # Update last activity for existing session
            self.sessions[session_id].last_activity = time.time()
            return session_id
        
        # Create new session
        new_session_id = session_id or self._generate_session_id()
        self.sessions[new_session_id] = ConversationSession(
            session_id=new_session_id,
            messages=[],
            last_activity=time.time(),
            created_at=time.time()
        )
        logger.info(f"Created new conversation session: {new_session_id}")
        return new_session_id
    
    def add_message(self, session_id: str, sender: str, text: str) -> bool:
        """Add a message to a session"""
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found, creating new one")
            session_id = self.get_or_create_session(session_id)
        
        session = self.sessions[session_id]
        
        # Check if we need to start a new session due to time gap
        if session.messages:
            last_message_time = session.messages[-1].timestamp
            current_time = time.time()
            time_diff_minutes = (current_time - last_message_time) / 60
            
            if time_diff_minutes > self.consecutive_timeout_minutes:
                logger.info(f"Time gap of {time_diff_minutes:.1f}min detected, starting new session")
                session_id = self.get_or_create_session()
                session = self.sessions[session_id]
        
        # Add message
        message = Message(
            sender=sender,
            text=text,
            timestamp=time.time(),
            session_id=session_id
        )
        
        session.messages.append(message)
        session.last_activity = time.time()
        
        # Trim messages if exceeding limit
        if len(session.messages) > self.max_messages_per_session:
            removed_count = len(session.messages) - self.max_messages_per_session
            session.messages = session.messages[removed_count:]
            logger.debug(f"Trimmed {removed_count} old messages from session {session_id}")
        
        logger.debug(f"Added message to session {session_id}: {sender} ({len(text)} chars)")
        return True
    
    def get_conversation_context(self, session_id: str, current_question: str) -> Tuple[str, Dict]:
        """Get optimized conversation context for the current question"""
        if session_id not in self.sessions:
            return "", {"session_id": session_id, "context_length": 0, "message_count": 0}
        
        session = self.sessions[session_id]
        messages = session.messages
        
        if not messages:
            return "", {"session_id": session_id, "context_length": 0, "message_count": 0}
        
        # Build conversation history
        conversation_parts = []
        total_length = 0
        
        # Start from most recent messages and work backwards
        for message in reversed(messages):
            message_text = f"{message.sender}: {message.text}"
            message_length = len(message_text)
            
            # Check if adding this message would exceed our limit
            if total_length + message_length > self.max_context_length:
                break
            
            conversation_parts.insert(0, message_text)
            total_length += message_length
        
        # Add current question
        current_question_text = f"user: {current_question}"
        if total_length + len(current_question_text) <= self.max_context_length:
            conversation_parts.append(current_question_text)
            total_length += len(current_question_text)
        
        context = "\n".join(conversation_parts)
        
        debug_info = {
            "session_id": session_id,
            "context_length": total_length,
            "message_count": len(conversation_parts),
            "total_session_messages": len(messages),
            "context_truncated": len(conversation_parts) < len(messages)
        }
        
        logger.debug(f"Generated context for session {session_id}: "
                    f"{len(conversation_parts)}/{len(messages)} messages, "
                    f"{total_length} chars")
        
        return context, debug_info
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        user_messages = [m for m in session.messages if m.sender == "user"]
        agent_messages = [m for m in session.messages if m.sender == "agent"]
        
        return {
            "session_id": session_id,
            "total_messages": len(session.messages),
            "user_messages": len(user_messages),
            "agent_messages": len(agent_messages),
            "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
            "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
            "session_age_minutes": (time.time() - session.created_at) / 60
        }
    
    def get_all_sessions_stats(self) -> Dict:
        """Get statistics for all sessions"""
        stats = {
            "total_sessions": len(self.sessions),
            "sessions": {}
        }
        
        for session_id in self.sessions:
            stats["sessions"][session_id] = self.get_session_stats(session_id)
        
        return stats

# Global conversation manager instance
conversation_manager = ConversationManager() 