import smtplib
from email.mime.text import MIMEText

correo = "josemr0420@gmail.com"
password = "lqxtdmkubmdxialf" 
destinatario = "pool.zapata@brinsa.com.co"

mensaje = MIMEText("Prueba de fuego de TALON por SSL")
mensaje['Subject'] = "Prueba de Bot SSL"
mensaje['From'] = correo
mensaje['To'] = destinatario

try:
    print("Conectando a Google por el puerto alternativo (465)...")
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465) 
    server.login(correo, password)
    server.send_message(mensaje)
    server.quit()
    print("✅ ¡ÉXITO TOTAL! El correo salió.")
except Exception as e:
    print(f"❌ FALLO: {e}")