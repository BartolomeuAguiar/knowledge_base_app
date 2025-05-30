import psycopg2
try:
    conn = psycopg2.connect(
        dbname="cdf_db",
        user="cdf_system_user",
        password="cdfsystem",
        host="localhost",
        port="5432"
    )
    print("Conexão bem-sucedida!")
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
