from database.database import get_connection

conn = get_connection()
cursor = conn.cursor()

# Lista as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tabelas no banco:")
for table in tables:
    print(f"  - {table['name']}")

# Conta registros em cada tabela
for table in tables:
    cursor.execute(f"SELECT COUNT(*) as count FROM {table['name']}")
    count = cursor.fetchone()['count']
    print(f"  {table['name']}: {count} registros")

conn.close()