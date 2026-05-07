# Usa una versión ligera de Python
FROM python:3.12-slim

# Crea una carpeta de trabajo en la nube
WORKDIR /app

# Copia todos tus archivos locales a la nube
COPY . /app

# Instala las librerías de tu requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto que usa Streamlit
EXPOSE 8501

# El comando que arranca la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]