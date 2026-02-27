import sqlite3
from pathlib import Path
import sys

# Adiciona o caminho do projeto ao sys.path se necessário
sys.path.append(str(Path(__file__).parent.parent.parent))

from yumi.core.database import get_connection, get_db_path_from_url

# Define o caminho do banco de dados
DB_PATH = get_db_path_from_url()
from yumi.core.database import get_db_path_from_url

DB_PATH = get_db_path_from_url()


def init_database():
    """Inicializa o banco de dados com todas as tabelas"""
    
    print(f"📁 Inicializando banco de dados em: {DB_PATH}")
    
    # Garante que o diretório existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Lê o arquivo SQL com as definições das tabelas
    sql_file = Path(__file__).parent / "models.sql"
    
    if not sql_file.exists():
        print(f"❌ Arquivo models.sql não encontrado em: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Conecta e executa o script
    try:
        conn = get_connection()
        
        # executescript() executa múltiplos comandos corretamente,
        # incluindo triggers com múltiplas linhas
        try:
            conn.executescript(sql_script)
            conn.commit()
            print("✅ Banco de dados inicializado com sucesso!")
        except sqlite3.Error as e:
            print(f"❌ Erro ao executar script SQL: {e}")
            conn.rollback()
            return False
        
        cursor = conn.cursor()
        
        # Lista as tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n📊 Tabelas criadas:")
        for table in tables:
            print(f"   - {table[0]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

def add_sample_data():
    """Opcional: Adiciona alguns dados de exemplo para teste"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    from database.database import gerar_uuid
    
    # Exemplo: Criar uma clínica de teste
    clinica_id = gerar_uuid()
    
    try:
        cursor.execute("""
            INSERT INTO clinica (id, nome, endereco, configuracoes, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, (
            clinica_id,
            "Clínica Veterinária Exemplo",
            "Rua Exemplo, 123",
            '{"tempo_padrao_consulta_minutos": 30}',
            1
        ))
        
        # Adicionar horário de funcionamento
        horarios = [
            (gerar_uuid(), clinica_id, 1, '08:00', '18:00'),  # Segunda
            (gerar_uuid(), clinica_id, 2, '08:00', '18:00'),  # Terça
            (gerar_uuid(), clinica_id, 3, '08:00', '18:00'),  # Quarta
            (gerar_uuid(), clinica_id, 4, '08:00', '18:00'),  # Quinta
            (gerar_uuid(), clinica_id, 5, '08:00', '18:00'),  # Sexta
        ]
        
        for horario in horarios:
            cursor.execute("""
                INSERT INTO clinica_funcionamento (id, clinica_id, dia_semana, hora_abertura, hora_fechamento)
                VALUES (?, ?, ?, ?, ?)
            """, horario)
        
        # Adicionar veterinários
        vet1_id = gerar_uuid()
        vet2_id = gerar_uuid()
        
        cursor.execute("""
            INSERT INTO veterinario (id, clinica_id, nome, especialidade, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, (vet1_id, clinica_id, "Dr. João Silva", "Clínica Geral", 1))
        
        cursor.execute("""
            INSERT INTO veterinario (id, clinica_id, nome, especialidade, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, (vet2_id, clinica_id, "Dra. Maria Santos", "Dermatologia", 1))
        
        conn.commit()
        print("✅ Dados de exemplo adicionados com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar dados de exemplo: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados Yumi...")
    if init_database():
        resposta = input("\nDeseja adicionar dados de exemplo? (s/N): ")
        if resposta.lower() == 's':
            add_sample_data()
        print("\n✨ Banco pronto para uso!")
    else:
        print("\n❌ Falha na inicialização do banco.")