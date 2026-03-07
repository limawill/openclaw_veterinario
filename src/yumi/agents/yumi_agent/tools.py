"""
tools.py — As "mãos" do Yumi Agent

Analogia:
    Imagine que o Yumi é um atendente de clínica.
    As tools são os SISTEMAS que ele pode consultar:
      - "Deixa eu ver os veterinários disponíveis..."
      - "Deixa eu verificar os horários livres..."
      - "Vou criar o agendamento para você..."

    O atendente NÃO acessa o banco diretamente.
    Ele usa os services (sistemas internos da clínica).

Decisão de design:
    Cada tool recebe `db: Session` como primeiro argumento.
    Isso mantém a arquitetura testável: nos testes, passamos um db mockado.
    O agente (yumi.py) é quem injeta o db quando chama a tool.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.services import agendamento_service, veterinario_service

# =====================================================
# FASE 1 — TOOLS DE CONSULTA (só lêtem dados)
# =====================================================


def buscar_veterinarios(db: Session, clinica_id: str) -> dict[str, Any]:
    """
    Retorna todos os veterinários ativos de uma clínica.

    Por que retorna dict e não o objeto SQLAlchemy?
    Porque o agente trabalha com dados simples (strings, listas, dicts).
    Não queremos que o agente acesse atributos do ORM diretamente —
    isso criaria um acoplamento forte entre o agente e o banco.

    Exemplo de retorno:
    {
        "sucesso": True,
        "total": 2,
        "veterinarios": [
            {"id": "...", "nome": "Dra. Ana", "especialidade": "Clínica Geral"}
        ]
    }
    """
    logger.debug(f"[Tool] buscar_veterinarios — clinica_id={clinica_id}")

    try:
        veterinarios = veterinario_service.get_veterinarios_by_clinica(db, clinica_id)

        # Serializa para dict simples — o agente não precisa do objeto ORM completo
        resultado = [
            {
                "id": v.id,
                "nome": v.nome,
                "especialidade": v.especialidade or "Clínica Geral",
                "ativo": v.ativo,
            }
            for v in veterinarios
            if v.ativo  # Só mostra veterinários ativos
        ]

        return {"sucesso": True, "total": len(resultado), "veterinarios": resultado}

    except Exception as e:
        logger.error(f"[Tool] Erro ao buscar veterinários: {e}")
        return {"sucesso": False, "erro": str(e), "veterinarios": []}


def listar_agendamentos_do_dia(
    db: Session,
    clinica_id: str,
    data: datetime | None = None,
) -> dict[str, Any]:
    """
    Retorna os agendamentos de um dia específico.
    Se `data` não for informada, usa o dia de HOJE.

    Por que uma tool separada só para o dia?
    Porque o caso mais comum do atendente é:
    "quais são os agendamentos de hoje?"
    ou "tem horário amanhã?"
    Uma tool focada é mais fácil de manter e testar.
    """
    logger.debug(f"[Tool] listar_agendamentos_do_dia — clinica_id={clinica_id}")

    data_ref = data or datetime.now()

    # Monta o intervalo do dia: 00:00:00 até 23:59:59
    inicio_do_dia = data_ref.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_do_dia = data_ref.replace(hour=23, minute=59, second=59, microsecond=0)

    try:
        agendamentos = agendamento_service.get_agendamentos(
            db=db,
            clinica_id=clinica_id,
            data_inicio=inicio_do_dia,
            data_fim=fim_do_dia,
        )

        resultado = [
            {
                "id": a.id,
                "nome_cliente": a.nome_cliente,
                "nome_pet": a.nome_pet,
                "inicio": a.data_hora_inicio.strftime("%H:%M"),
                "fim": a.data_hora_fim.strftime("%H:%M"),
                "status": a.status,
                "veterinario_id": a.veterinario_id,
            }
            for a in agendamentos
        ]

        return {
            "sucesso": True,
            "data": data_ref.strftime("%d/%m/%Y"),
            "total": len(resultado),
            "agendamentos": resultado,
        }

    except Exception as e:
        logger.error(f"[Tool] Erro ao listar agendamentos: {e}")
        return {"sucesso": False, "erro": str(e), "agendamentos": []}


def sugerir_horarios(
    db: Session,
    clinica_id: str,
    veterinario_id: str,
    data: datetime | None = None,
    duracao_minutos: int = 30,
) -> dict[str, Any]:
    """
    Sugere horários livres para um veterinário em um dia.

    Como funciona:
    1. Busca os agendamentos do dia para o veterinário
    2. Gera slots de X em X minutos dentro do horário comercial
    3. Remove os slots que têm conflito
    4. Retorna os slots livres

    Por que essa lógica está na tool e não no service?
    Porque é uma lógica de APRESENTAÇÃO (o que mostrar ao usuário),
    não uma regra de negócio (o service valida conflitos ao criar).
    A tool é o lugar certo para formatar dados para o agente.
    """
    logger.debug(f"[Tool] sugerir_horarios — vet={veterinario_id}")

    data_ref = data or datetime.now() + timedelta(days=1)  # padrão: amanhã
    inicio_do_dia = data_ref.replace(hour=8, minute=0, second=0, microsecond=0)
    fim_do_dia = data_ref.replace(hour=18, minute=0, second=0, microsecond=0)

    # Gera todos os slots possíveis do dia
    slots_possiveis: list[tuple[datetime, datetime]] = []
    atual = inicio_do_dia
    while atual + timedelta(minutes=duracao_minutos) <= fim_do_dia:
        slots_possiveis.append((atual, atual + timedelta(minutes=duracao_minutos)))
        atual += timedelta(minutes=duracao_minutos)

    try:
        # Agendamentos já existentes no dia para esse veterinário
        agendamentos = agendamento_service.get_agendamentos(
            db=db,
            clinica_id=clinica_id,
            veterinario_id=veterinario_id,
            data_inicio=inicio_do_dia,
            data_fim=fim_do_dia,
        )

        # Horarios já ocupados
        ocupados = [
            (a.data_hora_inicio, a.data_hora_fim)
            for a in agendamentos
            if a.status != "cancelado"
        ]

        # Filtra slots que conflitam com ocupados
        def tem_conflito(slot_inicio: datetime, slot_fim: datetime) -> bool:
            for ocup_inicio, ocup_fim in ocupados:
                if slot_inicio < ocup_fim and slot_fim > ocup_inicio:
                    return True
            return False

        slots_livres = [
            {
                "inicio": s.strftime("%H:%M"),
                "fim": f.strftime("%H:%M"),
                "inicio_iso": s.isoformat(),
                "fim_iso": f.isoformat(),
            }
            for s, f in slots_possiveis
            if not tem_conflito(s, f)
        ]

        return {
            "sucesso": True,
            "data": data_ref.strftime("%d/%m/%Y"),
            "duracao_minutos": duracao_minutos,
            "slots_livres": slots_livres,
            "total_livres": len(slots_livres),
        }

    except Exception as e:
        logger.error(f"[Tool] Erro ao sugerir horários: {e}")
        return {"sucesso": False, "erro": str(e), "slots_livres": []}


# =====================================================
# FASE 2 — TOOL DE AÇÃO (escreve dados)
# =====================================================


def criar_agendamento(
    db: Session,
    clinica_id: str,
    veterinario_id: str,
    nome_cliente: str,
    nome_pet: str,
    data_hora_inicio: datetime,
    data_hora_fim: datetime,
    telefone_cliente: str = "",
    origem: str = "chatbot",
) -> dict[str, Any]:
    """
    Cria um agendamento usando o service de agendamentos.

    Por que `origem` padrão é 'chatbot'?
    Porque essa tool é chamada via agente de IA —
    isso permite rastrear no banco que o agendamento veio
    do Yumi e não de um atendente humano.

    Por que a tool monta o schema e chama o service?
    Para não duplicar validações. O service já valida:
    - disponibilidade do veterinário
    - horário de funcionamento da clínica
    - conflitos com outros agendamentos
    """
    from yumi.schemas.schemas_agendamento import AgendamentoCreate

    logger.debug(f"[Tool] criar_agendamento — cliente={nome_cliente}, pet={nome_pet}")

    try:
        dados = AgendamentoCreate(
            clinica_id=clinica_id,
            veterinario_id=veterinario_id,
            nome_cliente=nome_cliente,
            nome_pet=nome_pet,
            telefone_cliente=telefone_cliente,
            data_hora_inicio=data_hora_inicio,
            data_hora_fim=data_hora_fim,
            origem=origem,
            status="agendado",
        )

        agendamento = agendamento_service.create_agendamento(db, dados)

        return {
            "sucesso": True,
            "agendamento_id": agendamento.id,
            "mensagem": (
                f"Consulta agendada com sucesso! ✅\n"
                f"Dia: {agendamento.data_hora_inicio.strftime('%d/%m/%Y')}\n"
                f"Horário: {agendamento.data_hora_inicio.strftime('%H:%M')} "
                f"até {agendamento.data_hora_fim.strftime('%H:%M')}\n"
                f"Pet: {agendamento.nome_pet}"
            ),
        }

    except Exception as e:
        logger.error(f"[Tool] Erro ao criar agendamento: {e}")
        return {"sucesso": False, "erro": str(e)}
