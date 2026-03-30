import duckdb

# El parámetro read_only=True permite entrar aunque Streamlit esté corriendo
con = duckdb.connect("datalake_local/talon_metastore.duckdb", read_only=True)

print("--- USUARIOS REGISTRADOS ---")
print(con.sql("SELECT * FROM usuarios_sistema").df())

con.close()