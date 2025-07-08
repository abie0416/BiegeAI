#!/usr/bin/env python3
"""
Test script for response sanitization functionality
"""
import os
import sys
import logging

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from agent.gemini_client import GeminiClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_response(response: str, gemini_client: GeminiClient) -> str:
    """
    Sanitize the final response to remove sensitive information
    
    Args:
        response: The original response from the AI model
        gemini_client: The Gemini client to use for sanitization
        
    Returns:
        Sanitized response with sensitive content removed or redacted
    """
    try:
        if not response or not response.strip():
            return response
        
        sanitization_prompt = f"""
You are sanitizing a response from an AI assistant to ensure it doesn't contain sensitive or inappropriate information.

Original response:
{response}

Your task is to remove or redact the following types of sensitive information:
1. Political views, opinions, or discussions
2. Sex-related content, innuendos, or explicit discussions
3. Personal complaints about relationships, family, or partners
4. Private personal information (addresses, phone numbers, etc.)
5. Financial information (bank details, salaries, etc.)
6. Any content that could be considered private or sensitive

Guidelines:
- Replace sensitive content with "[REDACTED]" or remove it entirely
- Keep the overall structure and helpfulness of the response
- Preserve neutral, factual information
- Maintain context where possible without revealing sensitive details
- If the entire response is sensitive, replace it with "[REDACTED]"
- Focus on providing helpful, safe information

Respond with the sanitized response that is safe for users.
"""
        
        sanitized_response = gemini_client.generate(sanitization_prompt)
        return sanitized_response
        
    except Exception as e:
        logger.error(f"❌ Error in response sanitization: {e}")
        return response  # Return original if sanitization fails

def test_response_sanitization():
    """Test the response sanitization functionality"""
    
    # You'll need to set your Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Please set GOOGLE_API_KEY environment variable")
        return
    
    # Initialize the Gemini client
    gemini_client = GeminiClient(google_api_key)
    
    # Test responses with sensitive content
    test_responses = [
        "Based on the chat history, John seems to have strong political views about the current government. He thinks they're doing a terrible job with the economy. Also, he mentioned that his wife keeps complaining about everything he does.",
        "The conversation included some explicit content that's not appropriate to discuss. Let me focus on the neutral parts instead.",
        "The meeting is scheduled for tomorrow at 3 PM. We need to discuss the quarterly budget and project timelines.",
        "Carol expressed frustration with her partner, saying they never listen and always prioritize work over their relationship. This is affecting their intimate life."
    ]
    
    print("🧪 Testing response sanitization...")
    print("=" * 50)
    
    # Process each test response
    for i, response in enumerate(test_responses, 1):
        print(f"\n📄 Test Response {i}:")
        print(f"Original: {response}")
        print("-" * 30)
        
        try:
            # Test the sanitization
            sanitized_response = sanitize_response(response, gemini_client)
            print(f"Sanitized: {sanitized_response}")
            
            # Check if content was redacted
            if '[REDACTED]' in sanitized_response:
                print("✅ Sensitive content was properly redacted")
            else:
                print("ℹ️  No sensitive content detected")
                
        except Exception as e:
            print(f"❌ Error during sanitization: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Response sanitization testing completed!")

if __name__ == "__main__":
    test_response_sanitization() 