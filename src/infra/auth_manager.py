"""
Manejo de Autenticación y Usuarios.
Utiliza hashing (bcrypt) para contraseñas y DuckDB local.
"""
import duckdb
import os
import bcrypt
import pandas as pd

DB_PATH = "datalake_local/talon_metastore.duckdb"

def inicializar_tabla_usuarios():
    """Crea la tabla de usuarios y la tabla de auditoria de accesos si no existen."""
    directorio = os.path.dirname(DB_PATH)
    if directorio and not os.path.exists(directorio):
        os.makedirs(directorio, exist_ok=True)
        
    with duckdb.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_sistema (
                email VARCHAR PRIMARY KEY,
                password_hash VARCHAR,
                fecha_registro TIMESTAMP
            )
        """)
        # Tabla para la trazabilidad de ingresos
        con.execute("""
            CREATE TABLE IF NOT EXISTS registro_accesos (
                email VARCHAR,
                fecha_ingreso TIMESTAMP
            )
        """)

def registrar_ingreso(email: str):
    """Guarda silenciosamente un registro cada vez que un usuario inicia sesion con exito."""
    try:
        with duckdb.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO registro_accesos (email, fecha_ingreso) VALUES (?, CURRENT_TIMESTAMP)", 
                (email,)
            )
    except Exception as e:
        print(f"Error registrando el acceso: {e}")

def registrar_usuario(email: str, password: str, dominio_permitido: str) -> tuple[bool, str]:
    """Registra un nuevo usuario validando el dominio corporativo y hasheando su contraseña."""
    email = email.lower().strip()
    
    if not email.endswith(dominio_permitido):
        return False, f"Solo se permiten correos del dominio {dominio_permitido}"
        
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
        
    # Hashear la contraseña por seguridad (nunca guardar en texto plano)
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    try:
        with duckdb.connect(DB_PATH) as con:
            # Verificar si existe
            resultado = con.execute("SELECT email FROM usuarios_sistema WHERE email = ?", (email,)).fetchone()
            if resultado:
                return False, "El usuario ya esta registrado."
                
            # Insertar
            con.execute(
                "INSERT INTO usuarios_sistema (email, password_hash, fecha_registro) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (email, password_hash)
            )
        return True, "Registro exitoso."
    except Exception as e:
        return False, f"Error en base de datos: {e}"

def validar_credenciales(email: str, password: str) -> bool:
    """Verifica si el correo existe y si la contraseña coincide con el hash."""
    email = email.lower().strip()
    try:
        with duckdb.connect(DB_PATH, read_only=True) as con:
            resultado = con.execute("SELECT password_hash FROM usuarios_sistema WHERE email = ?", (email,)).fetchone()
            
            if resultado:
                db_hash = resultado[0]
                # Comparar la contraseña ingresada con el hash guardado
                return bcrypt.checkpw(password.encode('utf-8'), db_hash.encode('utf-8'))
            return False
    except Exception as e:
        print(f"Error validando credenciales: {e}")
        return False