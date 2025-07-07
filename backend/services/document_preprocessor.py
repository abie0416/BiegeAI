"""
Document preprocessing service for cleaning and summarizing group chat history
"""
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from agent.gemini_client import GeminiClient
from concurrent.futures import ThreadPoolExecutor

# Get logger for this module
logger = logging.getLogger(__name__)

class DocumentPreprocessor:
    def __init__(self, google_api_key: str):
        self.gemini_client = GeminiClient(google_api_key)
        
    def preprocess_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Preprocess documents to clean and summarize group chat history in parallel.
        
        Args:
            documents: List of documents from Google Sheets
            
        Returns:
            List of preprocessed documents
        """
        logger.info(f"🧹 Starting document preprocessing for {len(documents)} documents (parallelized)...")
        
        def process_one(doc):
            try:
                original_content = doc.get('content', '')
                if not original_content.strip():
                    return None
                preprocessed_content = self._preprocess_single_document(original_content)
                if preprocessed_content and preprocessed_content.strip():
                    return {
                        'content': preprocessed_content,
                        'original_length': len(original_content),
                        'processed_length': len(preprocessed_content),
                        'compression_ratio': len(preprocessed_content) / len(original_content) if len(original_content) > 0 else 0
                    }
                else:
                    return None
            except Exception as e:
                logger.error(f"❌ Error preprocessing document: {e}")
                return doc
        
        # Use ThreadPoolExecutor to parallelize processing and preserve order
        preprocessed_docs = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(process_one, documents))
        preprocessed_docs = [r for r in results if r]
        
        logger.info(f"✅ Document preprocessing completed: {len(preprocessed_docs)} documents processed")
        return preprocessed_docs
    
    def _preprocess_single_document(self, content: str) -> str:
        """
        Preprocess a single document using AI to clean and summarize
        
        Args:
            content: Original document content
            
        Returns:
            Preprocessed content
        """
        try:
            # First, analyze the document structure
            analysis_prompt = self._create_analysis_prompt(content)
            analysis_response = self.gemini_client.generate(analysis_prompt)
            
            # Extract conversation segments based on analysis
            segments = self._extract_conversation_segments(content, analysis_response)
            
            if not segments:
                logger.warning("No conversation segments found, returning original content")
                return content
            
            # Process each segment
            processed_segments = []
            for segment in segments:
                processed_segment = self._process_conversation_segment(segment)
                if processed_segment:
                    processed_segments.append(processed_segment)
            
            if not processed_segments:
                logger.warning("No valid segments after processing, returning original content")
                return content
            
            # Combine processed segments
            final_content = self._combine_segments(processed_segments)
            
            return final_content
            
        except Exception as e:
            logger.error(f"❌ Error in single document preprocessing: {e}")
            return content
    
    def _create_analysis_prompt(self, content: str) -> str:
        """Create prompt for analyzing document structure"""
        return f"""
You are analyzing a document that may contain group chat history. Your task is to understand the structure and identify different conversations or topics.

Document content:
{content[:2000]}{'...' if len(content) > 2000 else ''}

Please analyze this document and respond with:
1. Number of distinct conversations/topics you can identify
2. Time periods or date indicators if present
3. Types of content (e.g., casual chat, work discussion, event planning)
4. Any patterns in message structure (e.g., timestamps, usernames, replies)

Respond in a structured format like:
- Conversations: [number]
- Time periods: [list any dates/times]
- Content types: [list types]
- Patterns: [list patterns]

Keep your response concise and focused on structure analysis.
"""
    
    def _extract_conversation_segments(self, content: str, analysis: str) -> List[Dict]:
        """
        Extract conversation segments based on AI analysis
        
        Args:
            content: Original content
            analysis: AI analysis response
            
        Returns:
            List of conversation segments
        """
        segments = []
        
        # Split by common conversation boundaries
        # Look for patterns like timestamps, "replying to", or clear topic shifts
        
        # Pattern 1: Split by timestamps (common in chat exports)
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*\d{1,2}/\d{1,2}/\d{2,4})'
        timestamp_splits = re.split(timestamp_pattern, content)
        
        if len(timestamp_splits) > 1:
            # Group timestamp with its content
            for i in range(0, len(timestamp_splits) - 1, 2):
                if i + 1 < len(timestamp_splits):
                    timestamp = timestamp_splits[i].strip()
                    segment_content = timestamp_splits[i + 1].strip()
                    if segment_content:
                        segments.append({
                            'content': f"{timestamp}\n{segment_content}",
                            'timestamp': timestamp,
                            'type': 'timestamp_segment'
                        })
        else:
            # Pattern 2: Split by "replying to" or similar indicators
            reply_pattern = r'(replying to|replied to|responding to|@\w+)'
            reply_splits = re.split(reply_pattern, content, flags=re.IGNORECASE)
            
            if len(reply_splits) > 1:
                current_segment = ""
                for i, part in enumerate(reply_splits):
                    if i % 2 == 0:  # Content part
                        current_segment += part
                    else:  # Reply indicator part
                        if current_segment.strip():
                            segments.append({
                                'content': current_segment.strip(),
                                'reply_indicator': part,
                                'type': 'reply_segment'
                            })
                        current_segment = part
                
                # Add the last segment
                if current_segment.strip():
                    segments.append({
                        'content': current_segment.strip(),
                        'type': 'final_segment'
                    })
            else:
                # Pattern 3: Split by large gaps or topic shifts
                # Look for multiple newlines or clear topic changes
                lines = content.split('\n')
                current_segment = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_segment:
                            segments.append({
                                'content': '\n'.join(current_segment),
                                'type': 'line_segment'
                            })
                            current_segment = []
                    else:
                        current_segment.append(line)
                
                # Add the last segment
                if current_segment:
                    segments.append({
                        'content': '\n'.join(current_segment),
                        'type': 'line_segment'
                    })
        
        # If no segments found, treat the entire content as one segment
        if not segments:
            segments.append({
                'content': content,
                'type': 'single_segment'
            })
        
        logger.info(f"📊 Extracted {len(segments)} conversation segments")
        return segments
    
    def _process_conversation_segment(self, segment: Dict) -> Optional[str]:
        """
        Process a single conversation segment using AI
        
        Args:
            segment: Segment dictionary with content and metadata
            
        Returns:
            Processed segment content or None if should be filtered out
        """
        content = segment.get('content', '')
        segment_type = segment.get('type', 'unknown')
        
        if not content.strip():
            return None
        
        # Create processing prompt based on segment type
        if segment_type == 'timestamp_segment':
            prompt = self._create_timestamp_segment_prompt(content)
        elif segment_type == 'reply_segment':
            prompt = self._create_reply_segment_prompt(content)
        else:
            prompt = self._create_general_segment_prompt(content)
        
        try:
            processed_content = self.gemini_client.generate(prompt)
            
            # Validate the processed content
            if self._is_meaningful_content(processed_content):
                return processed_content
            else:
                logger.debug(f"Filtered out segment as non-meaningful: {content[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing segment: {e}")
            return content  # Return original if processing fails
    
    def _create_timestamp_segment_prompt(self, content: str) -> str:
        """Create prompt for processing timestamp-based segments"""
        return f"""
You are processing a conversation segment from a group chat. This segment appears to be from a specific time period.

Original segment:
{content}

Your task:
1. Remove meaningless content like:
   - Laughing (haha, lol, 😂, etc.)
   - Emoji-only messages
   - Single word responses that don't add value
   - Repeated messages
   - Off-topic casual chat

2. Summarize the meaningful conversation into a concise format:
   - Keep important information, decisions, or discussions
   - Maintain context about who said what
   - Preserve key events or topics discussed
   - Use clear, structured language

3. If the segment contains multiple topics, separate them clearly

4. If the segment is mostly meaningless content, respond with "FILTER_OUT"

Respond with the cleaned and summarized content, or "FILTER_OUT" if the segment should be removed entirely.
"""
    
    def _create_reply_segment_prompt(self, content: str) -> str:
        """Create prompt for processing reply-based segments"""
        return f"""
You are processing a conversation segment that appears to be a reply or response in a group chat.

Original segment:
{content}

Your task:
1. Identify the main topic being discussed
2. Remove casual responses like:
   - "ok", "yes", "no" without context
   - Laughing or emoji responses
   - Off-topic comments
   - Repeated acknowledgments

3. Summarize the meaningful discussion:
   - Keep the question/issue being addressed
   - Keep the relevant response/solution
   - Maintain context about what was being replied to
   - Use clear, structured language

4. If this is just casual acknowledgment without substance, respond with "FILTER_OUT"

Respond with the cleaned and summarized content, or "FILTER_OUT" if the segment should be removed entirely.
"""
    
    def _create_general_segment_prompt(self, content: str) -> str:
        """Create prompt for processing general segments"""
        return f"""
You are processing a conversation segment from a group chat that needs cleaning and summarization.

Original segment:
{content}

Your task:
1. Analyze the content and identify:
   - Main topics or themes discussed
   - Important information or decisions
   - Casual vs. meaningful content

2. Remove or summarize:
   - Laughing, emojis, casual greetings
   - Off-topic discussions
   - Repeated information
   - Meaningless responses

3. Create a concise summary that:
   - Preserves important information
   - Maintains context about participants
   - Uses clear, structured language
   - Focuses on substance over style

4. If the segment is mostly meaningless content, respond with "FILTER_OUT"

Respond with the cleaned and summarized content, or "FILTER_OUT" if the segment should be removed entirely.
"""
    
    def _is_meaningful_content(self, content: str) -> bool:
        """Check if processed content is meaningful enough to keep"""
        if not content or content.strip() == "FILTER_OUT":
            return False
        
        # Check for minimum meaningful length
        if len(content.strip()) < 20:
            return False
        
        # Check for common meaningless patterns
        meaningless_patterns = [
            r'^\s*(ok|yes|no|maybe|sure|fine|good|bad)\s*$',
            r'^\s*(haha|lol|lmao|rofl)\s*$',
            r'^\s*[😀-🙏🌀-🗿]+$',  # Emoji-only
            r'^\s*filter_out\s*$'
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, content.strip(), re.IGNORECASE):
                return False
        
        return True
    
    def _combine_segments(self, segments: List[str]) -> str:
        """
        Combine processed segments into final document
        
        Args:
            segments: List of processed segment content
            
        Returns:
            Combined document content
        """
        if not segments:
            return ""
        
        # Combine segments with clear separators
        combined = "\n\n---\n\n".join(segments)
        
        # Clean up any excessive whitespace
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        combined = combined.strip()
        
        return combined
    
 