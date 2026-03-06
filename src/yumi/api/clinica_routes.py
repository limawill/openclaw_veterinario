from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from yumi.auth.dependencies import (
    Usuario,
    get_current_admin,
    get_current_atendente,
    get_current_clinica_id,
    verificar_mesma_clinica,
)
from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_clinica import (
    ClinicaCreate,
    ClinicaListResponse,
    ClinicaResponse,
    ClinicaUpdate,
)
from yumi.services import clinica_service

router = APIRouter()

# =====================================================
# POST - Criar clínica (APENAS ADMIN)
# =====================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClinicaResponse,
    summary="Criar nova clínica"
)
async def criar_clinica(
    clinica_data: ClinicaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin)  # 🔐 Só admin
):
    """
    Cria uma nova clínica.
    
    **Acesso:** Apenas administradores
    """
    logger.info(f"Admin {current_user.email} criando nova clínica")
    
    # Admin pode criar clínica (não precisa verificar mesma clínica)
    return clinica_service.create_clinica(db, clinica_data)

# =====================================================
# GET - Listar clínicas (ATENDENTE+)
# =====================================================


@router.get(
    "/",
    response_model=ClinicaListResponse,
    summary="Listar clínicas"
)
async def listar_clinicas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_atendente),  # 🔐 Atendente+
    clinica_id: str = Depends(get_current_clinica_id)        # 🔐 Pega do token
):
    """
    Lista clínicas do usuário.
    
    **Acesso:** Atendentes, administradores e devs
    **Multi-tenant:** Apenas dados da própria clínica
    """
    logger.debug(f"Usuário {current_user.email} listando clínicas")
    
    # Busca APENAS a clínica do usuário logado
    clinicas = clinica_service.listar_clinicas(db, clinica_id)
    
    return {
        "mensagem": f"Encontradas {len(clinicas)} clínicas",
        "total": len(clinicas),
        "clinicas": clinicas
    }

# =====================================================
# GET - Buscar clínica por ID (ATENDENTE+)
# =====================================================

@router.get(
    "/{clinica_id}",
    response_model=ClinicaResponse,
    summary="Buscar clínica por ID"
)
async def obter_clinica(
    clinica_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_atendente),  # 🔐 Atendente+
    _: None = Depends(verificar_mesma_clinica)               # 🔐 Valida multi-tenant
):
    """
    Busca uma clínica específica.
    
    **Acesso:** Atendentes, administradores e devs
    **Multi-tenant:** Apenas se for da mesma clínica
    """
    logger.debug(f"Usuário {current_user.email} buscando clínica {clinica_id}")
    
    clinica = clinica_service.get_clinica_by_id(db, clinica_id)
    return clinica

# =====================================================
# PUT - Atualizar clínica (APENAS ADMIN)
# =====================================================

@router.put(
    "/{clinica_id}",
    response_model=ClinicaResponse,
    summary="Atualizar clínica"
)
async def atualizar_clinica(
    clinica_id: str,
    clinica_data: ClinicaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),     # 🔐 Só admin
    _: None = Depends(verificar_mesma_clinica)               # 🔐 Valida multi-tenant
):
    """
    Atualiza dados de uma clínica.
    
    **Acesso:** Apenas administradores
    **Multi-tenant:** Apenas se for da mesma clínica
    """
    logger.info(f"Admin {current_user.email} atualizando clínica {clinica_id}")
    
    clinica = clinica_service.update_clinica(db, clinica_id, clinica_data)
    return clinica

# =====================================================
# DELETE - Desativar clínica (APENAS ADMIN)
# =====================================================

@router.delete(
    "/{clinica_id}",
    status_code=status.HTTP_200_OK,
    summary="Desativar clínica"
)
async def deletar_clinica(
    clinica_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),     # 🔐 Só admin
    _: None = Depends(verificar_mesma_clinica)               # 🔐 Valida multi-tenant
):
    """
    Desativa uma clínica (soft delete).
    
    **Acesso:** Apenas administradores
    **Multi-tenant:** Apenas se for da mesma clínica
    """
    logger.warning(f"Admin {current_user.email} desativando clínica {clinica_id}")
    
    clinica = clinica_service.delete_clinica(db, clinica_id)
    return {
        "mensagem": "Clínica desativada com sucesso",
        "clinica": {
            "id": clinica.id,
            "nome": clinica.nome,
            "ativo": clinica.ativo
        }
    }
