import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st

def enviar_correo_talon(correo_custodio: str, correo_auditor: str, dominio: str, score: float, total_errores: int, archivo_bytes: bytes) -> tuple[bool, str]:
    """Envía el reporte de saneamiento por correo SMTP."""
    
    # 1. Credenciales de la bóveda (asegúrate de ponerlas en .streamlit/secrets.toml)
    try:
        remitente_bot = st.secrets["smtp_email"]["correo"]
        password_bot = st.secrets["smtp_email"]["password"]
    except KeyError:
        return False, "Faltan credenciales SMTP en secrets.toml"

    # 2. Tu plantilla HTML Brinsa
    html_cuerpo = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333333; margin: 0; padding: 0; }}
            .data-table-td {{ font-size: 13px; text-transform: uppercase; color: #888888; padding-bottom: 10px; }}
            .data-table-td-val {{ font-size: 15px; color: #333333; text-align: right; font-weight: bold; padding-bottom: 10px; }}
        </style>
    </head>
    <body>
        <table align="center" width="100%" style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; border: 1px solid #e0e0e0; padding: 40px;">
            <tr>
                <td>
                    <img src="https://www.brinsa.com.co/sites/default/files/Brinsa_Full-color_127%20x%2040%20p%C3%ADxeles_1.png" width="120" style="margin-bottom: 20px;">
                    <h1 style="font-size: 26px; color: #000000; margin-bottom: 10px;">Acción Requerida: Saneamiento</h1>
                    <p style="font-size: 16px; color: #555555; margin-bottom: 30px;">
                        El usuario <strong>{correo_auditor}</strong> ejecutó una auditoría en T.A.L.O.N. y detectó anomalías.
                    </p>
                    <table width="100%" style="background-color: #f8f8f8; border: 1px solid #e0e0e0; padding: 20px;">
                        <tr><td class="data-table-td">Dominio</td><td class="data-table-td-val">{dominio}</td></tr>
                        <tr><td class="data-table-td">Score Global</td><td class="data-table-td-val" style="color: #FF2B00;">{score}%</td></tr>
                        <tr><td class="data-table-td">Registros a Sanear</td><td class="data-table-td-val">{total_errores}</td></tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # 3. Configurar Cabeceras
    mensaje = MIMEMultipart()
    mensaje['From'] = f"T.A.L.O.N. Auditoría <{remitente_bot}>"
    mensaje['To'] = correo_custodio
    mensaje['Subject'] = f"🚨 Alerta de Calidad: {dominio} ({score}%)"
    mensaje.add_header('reply-to', correo_auditor) 
    mensaje.attach(MIMEText(html_cuerpo, 'html'))

    # 4. Adjuntar Excel
    if archivo_bytes:
        part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        part.set_payload(archivo_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="Saneamiento_{dominio.replace(" ", "_")}.xlsx"')
        mensaje.attach(part)

# 5. Enviar (Usando la ruta SSL que venció al firewall)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente_bot, password_bot)
        server.send_message(mensaje)
        server.quit()
        return True, "Enviado con éxito"
    except Exception as e:
        return False, f"Error SMTP: {e}"