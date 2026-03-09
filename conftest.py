"""
Configuração global do pytest.
Adiciona o diretório src/ ao path para que os imports funcionem corretamente.
"""
import sys
from pathlib import Path

# Adiciona o diretório src/ ao PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Exclui scripts utilitários da coleta do pytest
collect_ignore = [
    "src/yumi/database/test_db.py",
    "src/yumi/database/seed.sql",
]
