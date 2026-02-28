from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.schemas.schemas_clinica import ClinicaCreate, ClinicaUpdate
from yumi.services import clinica_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_clinica(
    clinica_data: ClinicaCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova clínica."""
    
    # Chama o serviço (1 linha!)
    nova_clinica = clinica_service.create_clinica(db, clinica_data)
    
    # Monta resposta
    return {
        "mensagem": "Clínica criada com sucesso",
        "clinica": {
            "id": nova_clinica.id,
            "nome": nova_clinica.nome,
            "endereco": nova_clinica.endereco,
            "ativo": nova_clinica.ativo,
            "created_at": nova_clinica.created_at.isoformat() if nova_clinica.created_at else None
        }
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def listar_clinicas(db: Session = Depends(get_db)):
    """Lista todas as clínicas."""
    clinicas = clinica_service.listar_clinicas(db)
    return {
        "mensagem": f"Encontradas {len(clinicas)} clínicas",
        "clinicas": [
            {
                "id": c.id,
                "nome": c.nome,
                "endereco": c.endereco,
                "ativo": c.ativo,
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in clinicas
        ]
    }


@router.get("/{clinica_id}", status_code=status.HTTP_200_OK)
async def obter_clinica(
    clinica_id: str,  # ← Parâmetro vindo da URL
    db: Session = Depends(get_db)
):
    """Busca uma clínica específica por ID."""
    
    clinica = clinica_service.get_clinica_by_id(db, clinica_id)
    
    return {
        "mensagem": "Clínica encontrada",
        "clinica": {
            "id": clinica.id,
            "nome": clinica.nome,
            "endereco": clinica.endereco,
            "ativo": clinica.ativo,
            "created_at": clinica.created_at.isoformat() if clinica.created_at else None
        }
    }


@router.put("/{clinica_id}", status_code=status.HTTP_200_OK)
async def atualizar_clinica(
    clinica_id: str,
    clinica_data: ClinicaUpdate,  # ← Schema de update
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma clínica existente."""
    
    clinica = clinica_service.update_clinica(db, clinica_id, clinica_data)
    
    return {
        "mensagem": "Clínica atualizada com sucesso",
        "clinica": {
            "id": clinica.id,
            "nome": clinica.nome,
            "endereco": clinica.endereco,
            "ativo": clinica.ativo,
            "configuracoes": clinica.configuracoes,
            "updated_at": clinica.updated_at.isoformat() if clinica.updated_at else None
        }
    }


@router.delete("/{clinica_id}",  status_code=status.HTTP_200_OK)
async def deletar_clinica(
    clinica_id: str,
    db: Session = Depends(get_db)
):
    """Deleta (ou desativa) uma clínica."""
    
    clinica = clinica_service.delete_clinica(db, clinica_id)
    
    return {
        "mensagem": "Clínica desativada com sucesso",
        "clinica": {
            "id": clinica.id,
            "nome": clinica.nome,
            "ativo": clinica.ativo  # ← False agora
        }
    }