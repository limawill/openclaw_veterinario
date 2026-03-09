from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from yumi.api.agendamento_routes import router as agendamento_router
from yumi.api.agent_routes import router as agent_router
from yumi.api.clinica_func_routes import router as clinica_func_router
from yumi.api.clinica_routes import router as clinica_router
from yumi.api.integracao_routes import router as integracao_router
from yumi.api.routes import router
from yumi.api.usuario_routes import router as usuario_router
from yumi.api.veterinario_routes import router as veterinario_router
from yumi.auth.auth_routes import router as auth_router
from yumi.core.config import settings
from yumi.core.limiter import limiter
from yumi.core.logger import logger

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Registrar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(auth_router) 
app.include_router(router, prefix="")
app.include_router(clinica_router, prefix="/api/v1/clinicas", tags=["Clínicas"])
app.include_router(clinica_func_router, prefix="/api/v1/clinicas/{clinica_id}/funcionamento", tags=["Funcionamento"])
app.include_router(usuario_router, prefix="/api/v1/usuarios", tags=["Usuários"])
app.include_router(veterinario_router, prefix="/api/v1/veterinarios", tags=["Veterinários"])
app.include_router(agendamento_router, prefix="/api/v1/agendamentos", tags=["Agendamentos"])
app.include_router(integracao_router, prefix="/api/v1/integracoes", tags=["Integrações"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["Yumi Agent"])


# Eventos de startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação inicia."""
    logger.info(
        f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION} "
        f"- Ambiente: {settings.ENVIRONMENT}"
    )
    
    print(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Ambiente: {settings.ENVIRONMENT}")
    print(f"🔗 Documentação: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a aplicação encerra."""
    logger.info(f"Encerrando {settings.APP_NAME}")
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
