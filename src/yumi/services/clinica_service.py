from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models import Clinica
from yumi.schemas.schemas_clinica import ClinicaCreate, ClinicaUpdate
from yumi.utils.uuid_generator import gerar_uuid


def create_clinica(db: Session, clinica_data: ClinicaCreate):
    """
    Regra de negócio para criar uma clínica.
    Retorna a clínica criada ou levanta exceção.
    """
    logger.debug(f"Iniciando criação de clínica: {clinica_data.nome}")
    
    # 1. Verifica duplicidade
    clinica_existente = db.query(Clinica).filter(
        Clinica.nome == clinica_data.nome
    ).first()
    
    if clinica_existente:
        logger.warning(
            f"Tentativa de criar clínica duplicada: {clinica_data.nome} "
            f"(ID: {clinica_existente.id})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma clínica com este nome"
        )
    
    # 2. Cria instância
    nova_clinica = Clinica(
        id=gerar_uuid(),
        nome=clinica_data.nome,
        endereco=clinica_data.endereco,
        configuracoes=clinica_data.configuracoes or {},
        ativo=True
    )
    
    # 3. Persiste
    try:
        db.add(nova_clinica)
        db.commit()
        db.refresh(nova_clinica)
        logger.info(f"Clínica criada com sucesso: {nova_clinica.nome} (ID: {nova_clinica.id})")
        return nova_clinica
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar clínica {clinica_data.nome}", exception=e)
        raise


def listar_clinicas(db: Session):
    """
    Regra de negócio para listar clínicas.
    Retorna uma lista de clínicas ativas.
    """
    return db.query(Clinica).filter(Clinica.ativo == True).all()


def get_clinica_by_id(db: Session, clinica_id: str):
    """
    Busca uma clínica específica por ID.
    Retorna a clínica ou levanta 404 se não existir.
    """
    # Remove espaços em branco que podem vir da URL
    clinica_id = clinica_id.strip()
    
    logger.debug(f"Buscando clínica com ID: {clinica_id}")
    
    clinica = db.query(Clinica).filter(Clinica.id == clinica_id).first()
    
    if not clinica:
        # Debug: lista os IDs disponíveis
        ids_disponiveis = [c.id for c in db.query(Clinica).all()]
        logger.warning(
            f"Clínica não encontrada - ID solicitado: {clinica_id} "
            f"- Total de clínicas disponíveis: {len(ids_disponiveis)}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "mensagem": f"Clínica com ID '{clinica_id}' não encontrada",
                "id_recebido": clinica_id,
                "tamanho_id": len(clinica_id),
                "ids_disponiveis": ids_disponiveis
            }
        )
    
    logger.debug(f"Clínica encontrada: {clinica.nome} (ID: {clinica.id})")
    return clinica


def update_clinica(db: Session, clinica_id: str, clinica_data: ClinicaUpdate):
    """
    Atualiza os dados de uma clínica existente.
    """
    # 1. Busca a clínica (reusa função anterior)
    clinica = get_clinica_by_id(db, clinica_id)
    
    # 2. Atualiza apenas os campos enviados
    update_data = clinica_data.model_dump(exclude_unset=True)  # ← Pega só o que veio
    
    for field, value in update_data.items():
        setattr(clinica, field, value)
    
    # 3. Salva
    db.commit()
    db.refresh(clinica)
    
    return clinica


def delete_clinica(db: Session, clinica_id: str):
    """
    Deleta (ou desativa) uma clínica.
    """
    clinica = get_clinica_by_id(db, clinica_id)
    clinica.ativo = False
    db.commit()
    db.refresh(clinica)
    return clinica

