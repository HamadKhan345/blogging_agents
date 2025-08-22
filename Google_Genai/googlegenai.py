from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
import os


class google_structured_output:
    def __init__(self):
        pass
    
    def call_google_structured_output(self, prompt, pydantic_model, model="gemini-2.5-flash", max_tokens=15000, temperature=0.7, thinking_budget=0):
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=pydantic_model,
        temperature=temperature,
        max_output_tokens=max_tokens,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        try:
            validated = response.parsed 
            return validated
        except Exception as e:
            raise ValueError(f"Error parsing Gemini output: {e}\nRaw output: {response.text}")