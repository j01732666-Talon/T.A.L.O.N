import os
import google.generativeai as genai

# Configurar con la clave desde la variable de entorno o secrets.toml
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

print("Modelos disponibles para generar texto:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)