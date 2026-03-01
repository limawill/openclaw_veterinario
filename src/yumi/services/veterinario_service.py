from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models.agendamento import Agendamento
from yumi.models.veterinario import Veterinario
from yumi.utils.tools import Tools
from yumi.utils.uuid_generator import gerar_uuid


def create_veterinario(db: Session, veterinario_data):
    """
    Regra de negócio para cadastrar um novo profissional.
    Retorna o veterinário criado ou levanta exceção.
    """
    logger.debug(f"Iniciando criação de veterinário: {veterinario_data.nome}")
    
    # 1. Verifica duplicidade
    veterinario_existente = db.query(Veterinario).filter(
        Veterinario.email == veterinario_data.email
    ).first()
    
    if veterinario_existente:
        logger.warning(
            f"Tentativa de criar veterinário duplicado: {veterinario_data.email} "
            f"(ID: {veterinario_existente.id})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um veterinário com este email"
        )
    
    # 2. Cria instância
    novo_veterinario = Veterinario(
        id=gerar_uuid(),
        clinica_id=veterinario_data.clinica_id,
        email=veterinario_data.email,
        nome=veterinario_data.nome,
        especialidade=veterinario_data.especialidade,
        ativo=veterinario_data.ativo
    )
    
    # 3. Persiste
    try:
        db.add(novo_veterinario)
        db.commit()
        db.refresh(novo_veterinario)
        logger.info(f"Veterinário criado com sucesso: {novo_veterinario.email} (ID: {novo_veterinario.id})")
        return novo_veterinario
    except Exception:
        db.rollback()
        logger.error(f"Erro ao criar veterinário {veterinario_data.email}", exc_info=True)
        raise


def get_veterinario_by_id(db: Session, veterinario_id: str):
    """
    Busca um veterinário específico por ID.
    Retorna o veterinário ou levanta 404 se não existir.
    """
    logger.debug(f"Buscando veterinário com ID: {veterinario_id}")
    
    # Remove espaços em branco que podem vir da URL
    veterinario_id = Tools.remove_espaco_string(veterinario_id)
    
    veterinario = db.query(Veterinario).filter(Veterinario.id == veterinario_id).first()
    
    if not veterinario:
        logger.warning(f"Veterinário não encontrado - ID solicitado: {veterinario_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Veterinário com ID '{veterinario_id}' não encontrado"
        )
    
    logger.debug(f"Veterinário encontrado: {veterinario.nome} (ID: {veterinario.id})")
    return veterinario


def get_veterinarios_by_clinica(db: Session, clinica_id: str):
    """
    Busca todos os veterinários vinculados a uma clínica.
    Retorna lista de veterinários ou vazia se não houver.
    """
    logger.debug(f"Buscando veterinários para clínica ID: {clinica_id}")
    # Remove espaços em branco que podem vir da URL
    clinica_id = Tools.remove_espaco_string(clinica_id)
    usuarios = db.query(Veterinario).filter(Veterinario.clinica_id == clinica_id).all()
    
    logger.info(f"{len(usuarios)} veterinário(s) encontrados para clínica ID: {clinica_id}")
    return usuarios


def atualizar_veterinario(db: Session, veterinario_id: str, veterinario_data):
    """
    Regra de negócio para atualizar um usuário.
    Retorna o veterinário atualizado ou levanta exceção.
    """
    logger.debug(f"Iniciando atualização de veterinário ID: {veterinario_id}")
    
    veterinario = get_veterinario_by_id(db, veterinario_id)
    
    # Atualiza campos se foram fornecidos
    if veterinario_data.nome is not None:
        veterinario.nome = veterinario_data.nome
    if veterinario_data.email is not None:
        # Verifica duplicidade de email
        email_existente = db.query(Veterinario).filter(
            Veterinario.email == veterinario_data.email,
            Veterinario.id != veterinario_id  # Ignora o próprio veterinário
        ).first()
        if email_existente:
            logger.warning(
                f"Tentativa de atualizar veterinário com email duplicado: {veterinario_data.email} "
                f"(ID existente: {email_existente.id})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro veterinário com este email"
            )
        veterinario.email = veterinario_data.email
    if veterinario_data.especialidade is not None:
        veterinario.especialidade = veterinario_data.especialidade
    if veterinario_data.ativo is not None:
        veterinario.ativo = veterinario_data.ativo
    
    # Persiste alterações
    try:
        db.commit()
        db.refresh(veterinario)
        logger.info(f"Veterinário atualizado com sucesso: {veterinario.nome} (ID: {veterinario.id})")
        return veterinario
    except Exception:
        db.rollback()
        logger.error(f"Erro ao atualizar veterinário ID: {veterinario_id}", exc_info=True)
        raise


def delete_veterinario(db: Session, veterinario_id: str):
    """
    Regra de negócio para deletar um veterinário.
    Retorna mensagem de sucesso ou levanta exceção.
    """
    logger.debug(f"Iniciando exclusão de veterinário ID: {veterinario_id}")
    veterinario = get_veterinario_by_id(db, veterinario_id)
    veterinario.ativo = False
    db.commit()
    db.refresh(veterinario)
    return veterinario


# src/yumi/services/veterinario_service.py


def get_agendamentos_por_veterinario(
    db: Session, 
    veterinario_id: str,
    apenas_ativos: bool = True,
    data_inicio=None,
    data_fim=None
):
    """
    Busca todos os agendamentos de um veterinário específico.
    
    Args:
        db: Sessão do banco
        veterinario_id: ID do veterinário
        apenas_ativos: Se True, retorna apenas agendamentos não cancelados
        data_inicio: Filtrar a partir desta data (opcional)
        data_fim: Filtrar até esta data (opcional)
    
    Returns:
        Lista de agendamentos do veterinário
    """
    logger.debug(f"Buscando agendamentos para veterinário ID: {veterinario_id}")
    
    # 1. Primeiro verifica se o veterinário existe
    veterinario = get_veterinario_by_id(db, veterinario_id)
    
    # 2. Constrói a query base
    query = db.query(Agendamento).filter(
        Agendamento.veterinario_id == veterinario_id
    )
    
    # 3. Filtros opcionais
    if apenas_ativos:
        # Exclui cancelados (status diferente de 'cancelado')
        query = query.filter(Agendamento.status != 'cancelado')
    
    if data_inicio:
        query = query.filter(Agendamento.data_hora_inicio >= data_inicio)
    
    if data_fim:
        query = query.filter(Agendamento.data_hora_fim <= data_fim)
    
    # 4. Ordena por data (mais recentes primeiro)
    query = query.order_by(Agendamento.data_hora_inicio.desc())
    
    agendamentos = query.all()
    
    logger.info(
        f"{len(agendamentos)} agendamento(s) encontrados "
        f"para veterinário {veterinario.nome} (ID: {veterinario_id})"
    )
    
    return agendamentos
