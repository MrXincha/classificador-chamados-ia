import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    print("Buscando modelos disponíveis...")
    print("-" * 30)

    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

except Exception as e:
    print(f"Ocorreu um erro: {e}")