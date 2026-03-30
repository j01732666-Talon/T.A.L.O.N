import duckdb

# Ruta exacta asumiendo que ejecutas el script desde la carpeta raiz
DB_PATH = "datalake_local/talon_metastore.duckdb" 

try:
    with duckdb.connect(DB_PATH) as con:
        # Borramos todos los registros de la tabla de usuarios
        con.execute("DELETE FROM usuarios_sistema")
        print("Registros de usuarios eliminados con exito.")
        print("Ya puedes volver a la aplicacion para registrar tu cuenta nuevamente con encriptacion activa.")
except Exception as e:
    print(f"Ocurrio un error: {e}")