from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yumi.api.agendamento_routes import router as agendamento_router
from yumi.api.clinica_func_routes import router as clinica_func_router
from yumi.api.clinica_routes import router as clinica_router
from yumi.api.integracao_routes import router as integracao_router
from yumi.api.routes import router
from yumi.api.usuario_routes import router as usuario_router
from yumi.api.veterinario_routes import router as veterinario_router
from yumi.core.config import settings

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
app.include_router(router, prefix="")
app.include_router(clinica_router, prefix="/api/v1/clinicas", tags=["Clínicas"])
app.include_router(clinica_func_router, prefix="/api/v1/clinicas/funcionamento", tags=["Funcionamento"])
app.include_router(usuario_router, prefix="/api/v1/usuarios", tags=["Usuários"])
app.include_router(veterinario_router, prefix="/api/v1/veterinarios", tags=["Veterinários"])
app.include_router(agendamento_router, prefix="/api/v1/agendamentos", tags=["Agendamentos"])
app.include_router(integracao_router, prefix="/api/v1/integracoes", tags=["Integrações"])


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
