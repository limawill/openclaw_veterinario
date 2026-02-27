#!/usr/bin/env python
"""Script para rodar a aplicação com as configurações do .env"""

import sys
from pathlib import Path

# Adicionar src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from yumi.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "yumi.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
