from google import genai
from google.genai import types



class google_structured_output:
    def __init__(self):
        pass
    
    def call_google_structured_output(self, prompt, pydantic_model, model="gemini-2.5-flash", max_tokens=65536, temperature=0.5):
        client = genai.Client()
        config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=pydantic_model,
        temperature=temperature,
        maxOutputTokens=max_tokens,
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