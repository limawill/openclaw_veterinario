"""Ponto de entrada da aplicação Yumi Agent."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yumi.core.config import settings
from yumi.api.routes import router

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router, prefix="")  # Sem prefixo para rotas principais

# Eventos de startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação inicia."""
    print(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Ambiente: {settings.ENVIRONMENT}")
    print(f"🔗 Documentação: http://{settings.HOST}:{settings.PORT}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a aplicação encerra."""
    print("👋 Encerrando Yumi Agent...")

# Para execução direta (útil para debugging)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "yumi.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )