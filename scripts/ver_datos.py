import duckdb

# Ruta a la base de datos
DB_PATH = "datalake_local/talon_metastore.duckdb"

print("\n" + "="*50)
print(" TABLA: USUARIOS DEL SISTEMA")
print("="*50)
try:
    # Usamos read_only=True para que no interfiera si Streamlit está abierto
    with duckdb.connect(DB_PATH, read_only=True) as con:
        df_usuarios = con.execute("SELECT email, fecha_registro, password_hash FROM usuarios_sistema").df()
        
        # Recortamos el hash visualmente para que la tabla no se desconfigure
        if not df_usuarios.empty:
            df_usuarios['password_hash'] = df_usuarios['password_hash'].str[:15] + "..."
            
        print(df_usuarios.to_string(index=False))
except Exception as e:
    print(f"Error o tabla no encontrada: {e}")

print("\n" + "="*50)
print(" TABLA: HISTORIAL DE AUDITORÍAS")
print("="*50)
try:
    with duckdb.connect(DB_PATH, read_only=True) as con:
        # Traemos solo las columnas principales para que quepan en la pantalla
        consulta = """
            SELECT id_ejecucion, fecha, usuario, dominio, total_registros, score_global
            FROM historial_auditorias
            ORDER BY fecha DESC
            LIMIT 5
        """
        df_auditorias = con.execute(consulta).df()
        
        # Formatear el score para que se vea como porcentaje
        if not df_auditorias.empty:
            df_auditorias['score_global'] = df_auditorias['score_global'].apply(lambda x: f"{x:.2f}%")
            
        print(df_auditorias.to_string(index=False))
except Exception as e:
    print(f"Error o tabla no encontrada: {e}")
print("\n")