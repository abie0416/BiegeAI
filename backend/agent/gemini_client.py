# Direct Google Generative AI integration
import os
import google.generativeai as genai
from typing import Optional

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            if system_prompt:
                # Combine system prompt and user prompt
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"[Gemini API Error] {str(e)}" 