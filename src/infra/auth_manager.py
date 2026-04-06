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
    """
    Inicializa la base de datos local DuckDB creando las tablas necesarias para el sistema.
    
    Crea el directorio de almacenamiento si no existe. Luego, define la tabla 'usuarios_sistema' 
    para almacenar las credenciales (hasheadas) y la tabla 'registro_accesos' para mantener 
    la trazabilidad de los ingresos a la plataforma.
    """
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
    """
    Registra en la base de datos el momento exacto en el que un usuario inicia sesión correctamente.
    
    Esta función opera de manera silenciosa (captura las excepciones sin interrumpir el flujo) 
    para poblar la tabla de auditoría 'registro_accesos'.
    
    Args:
        email (str): El correo electrónico del usuario que acaba de iniciar sesión.
    """
    try:
        with duckdb.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO registro_accesos (email, fecha_ingreso) VALUES (?, CURRENT_TIMESTAMP)", 
                (email,)
            )
    except Exception as e:
        print(f"Error registrando el acceso: {e}")

def registrar_usuario(email: str, password: str, dominio_permitido: str) -> tuple[bool, str]:
    """
    Crea una nueva cuenta de usuario validando reglas de negocio y asegurando la contraseña.
    
    Verifica que el correo pertenezca al dominio corporativo permitido y que la contraseña 
    cumpla con la longitud mínima. Posteriormente, genera un hash seguro usando bcrypt 
    antes de almacenar la información en la base de datos DuckDB.
    
    Args:
        email (str): El correo electrónico proporcionado para el registro.
        password (str): La contraseña en texto plano ingresada por el usuario.
        dominio_permitido (str): El dominio corporativo exigido (ej. '@empresa.com').
        
    Returns:
        tuple[bool, str]: 
            - bool: True si el registro fue exitoso, False si falló alguna validación o si el usuario ya existe.
            - str: Mensaje descriptivo con el resultado de la operación.
    """
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
    """
    Comprueba la autenticidad de las credenciales de un usuario durante el inicio de sesión.
    
    Busca el correo electrónico en la base de datos local y, si lo encuentra, compara 
    la contraseña ingresada (en texto plano) contra el hash seguro almacenado utilizando bcrypt.
    
    Args:
        email (str): El correo electrónico del usuario que intenta ingresar.
        password (str): La contraseña en texto plano ingresada en el formulario.
        
    Returns:
        bool: True si las credenciales son correctas y coinciden, False en caso contrario o si ocurre un error.
    """
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