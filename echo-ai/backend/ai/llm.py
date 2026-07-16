import os
import time
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env at startup
load_dotenv()
print("=" * 60)
print("Current Working Directory:", os.getcwd())
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
print("MODEL_NAME:", os.getenv("MODEL_NAME"))
print("=" * 60)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
        
        try:
            self.temperature = float(os.getenv("TEMPERATURE", "0.0"))
        except ValueError:
            self.temperature = 0.0
            
        try:
            self.max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        except ValueError:
            self.max_tokens = 1024
            
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)

    def generate_response(self, system_prompt: str, user_message: str, retries: int = 2) -> str:
        """
        Sends system and user messages to the Groq API.
        Includes error handling, retries, and returning the raw string content.
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Ensure GROQ_API_KEY is configured in your .env file.")
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        last_error = None
        for attempt in range(retries + 1):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=15.0  # 15 seconds timeout
                )
                return completion.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(1)  # Brief backoff before retrying
                    continue
                    
        raise RuntimeError(f"Failed to retrieve response from Groq API: {str(last_error)}")
