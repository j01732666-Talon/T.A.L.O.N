import google.generativeai as genai

# Reemplaza con tu clave real solo para esta prueba
genai.configure(api_key="TU_CLAVE_AQUI")

print("Modelos disponibles para generar texto:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)