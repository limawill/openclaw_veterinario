"""
yumi.py — O cérebro do Yumi Agent

Analogia:
    O Yumi é como um atendente de clínica virtual.
    Ele RECEBE a mensagem do cliente, ENTENDE o que o cliente quer
    e EXECUTA a ação correta usando as tools.

    Mensagem recebida:  "Quero agendar para amanhã"
    Yumi entende:        intenção = AGENDAR
    Yumi executa:        busca veterinários → sugere horários → responde

ARQUITETURA EM FASES:

    Fase 1 (atual — MVP):
        Detecção de intenção por palavras-chave simples.
        Simples, funcional, testavél.

    Fase 2 (futuro — OpenClaw):
        Substituir `_detectar_intencao()` por chamada ao LLM.
        O resto do código não muda — só o método de detecção evolui.
        Essa é a vantagem de isolar a detecção num método próprio.

Por que o agente não instancia o db (Session) internamente?
    Porque o db é um recurso de infraestrutura — quem deve fornecer
    é a rota (via Depends(get_db)) ou o teste (via fixture).
    O agente foca no que sabe fazer: entender e responder.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from yumi.agents.yumi_agent import tools
from yumi.core.logger import logger

# =====================================================
# FASE 1 — MAPA DE INTENÇÕES
# =====================================================
# Uma intenção é o QUE o usuário quer fazer.
# Por enquanto detectamos por palavras-chave simples.
# No futuro, um LLM fará isso de forma muito mais precisa.

class Intencao(str, Enum):
    LISTAR_VETERINARIOS = "listar_veterinarios"
    VER_AGENDAMENTOS = "ver_agendamentos"
    AGENDAR_CONSULTA = "agendar_consulta"
    VER_HORARIOS = "ver_horarios"
    DESCONHECIDO = "desconhecido"


# Mapa de palavras-chave → intenção
# Ordem importa: mais específico primeiro
_PALAVRAS_CHAVE: list[tuple[list[str], Intencao]] = [
    # Palavras que sugerem querer marcar/agendar
    (
        ["agendar", "marcar", "consulta", "quero marcar", "quero agendar", "amanhã"],
        Intencao.AGENDAR_CONSULTA,
    ),
    # Palavras que sugerem querer ver horários disponíveis
    (
        ["horário", "horario", "disponível", "disponivel", "vaga", "livre"],
        Intencao.VER_HORARIOS,
    ),
    # Palavras que sugerem ver a agenda do dia
    (
        ["agendamento", "agenda", "consultas", "marcados"],
        Intencao.VER_AGENDAMENTOS,
    ),
    # Palavras que sugerem querer ver os veterinários
    (
        ["veterinário", "veterinario", "médico", "dr", "dra", "profissional"],
        Intencao.LISTAR_VETERINARIOS,
    ),
]


class YumiAgent:
    """
    Agente principal do sistema Yumi.

    Recebe mensagens de texto do usuário e responde
    executando ações via tools.

    Uso básico:
        agent = YumiAgent(clinica_id="uuid-da-clinica", db=db_session)
        resposta = agent.handle_message("Quais veterinários você tem?")
        print(resposta["resposta"])
    """

    def __init__(self, clinica_id: str, db: Session):
        """
        Por que clinica_id no __init__?
        Porque o agente SEMPRE trabalha dentro de uma clínica específica.
        Isso garante o isolamento multi-tenant: o Yumi de uma clínica
        NUNCA acessa dados de outra clínica.

        Por que db no __init__ e não em cada chamada?
        Para manter a interface simples: quem cria o agente
        fornece o db uma única vez, e ele é reaproveitado
        em todas as operações daquela conversa.
        """
        self.clinica_id = clinica_id
        self.db = db
        # Contexto da conversa — será útil quando integrar com LLM
        self.contexto: dict[str, Any] = {}
        logger.debug(f"[YumiAgent] Inicializado para clinica_id={clinica_id}")

    # =====================================================
    # MÉTODO PRINCIPAL
    # =====================================================

    def handle_message(
        self,
        message: str,
        historico: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Ponto de entrada do agente.

        Fluxo:
        1. Normaliza a mensagem (lower case, sem espaços extras)
        2. Detecta intenção
        3. Chama o handler correto
        4. Retorna resposta estruturada

        Args:
            message:   Texto enviado pelo usuário.
            historico: Histórico das últimas mensagens da sessão no formato
                       [{"role": "user"|"assistant", "message": "..."}].
                       Fase 1 (MVP): ignorado — detecção por keyword não usa contexto.
                       Fase 2 (LLM): será passado como context window ao modelo.

        Retorna sempre um dict com:
        {
            "intencao": str,
            "resposta": str,        ← texto para mostrar ao usuário
            "dados": dict | None    ← dados extras (para o frontend usar)
        }
        """
        logger.info(
            f"[YumiAgent] Mensagem recebida: '{message}' "
            f"| Histórico: {len(historico or [])} msgs"
        )

        mensagem_normalizada = message.lower().strip()
        intencao = self._detectar_intencao(mensagem_normalizada)

        logger.debug(f"[YumiAgent] Intenção detectada: {intencao}")

        # Despacha para o handler correto
        handlers = {
            Intencao.LISTAR_VETERINARIOS: self._handle_listar_veterinarios,
            Intencao.VER_AGENDAMENTOS:    self._handle_ver_agendamentos,
            Intencao.AGENDAR_CONSULTA:    self._handle_agendar_consulta,
            Intencao.VER_HORARIOS:        self._handle_ver_horarios,
            Intencao.DESCONHECIDO:        self._handle_desconhecido,
        }

        handler = handlers[intencao]
        resultado = handler(mensagem_normalizada)
        resultado["intencao"] = intencao.value

        return resultado

    # =====================================================
    # DETECÇÃO DE INTENÇÃO (Fase 1 — keywords)
    # =====================================================

    def _detectar_intencao(self, mensagem: str) -> Intencao:
        """
        Detecta a intenção por palavras-chave.

        Por que método separado e não inline no handle_message?
        Para isolar a lógica de detecção.
        Na Fase 2, este método será substituído por uma
        chamada ao LLM (OpenClaw) sem alterar o restante.
        """
        for palavras, intencao in _PALAVRAS_CHAVE:
            if any(p in mensagem for p in palavras):
                return intencao
        return Intencao.DESCONHECIDO

    # =====================================================
    # HANDLERS — um por intenção
    # =====================================================
    # Por que handlers separados e não um grande if/elif?
    # Cada handler tem uma responsabilidade clara.
    # É fácil de testar isoladamente.
    # É fácil de adicionar novos sem mexer nos existentes.

    def _handle_listar_veterinarios(self, mensagem: str) -> dict[str, Any]:
        """Handler para: 'quais veterinários vocês têm?'"""
        resultado = tools.buscar_veterinarios(self.db, self.clinica_id)

        if not resultado["sucesso"] or resultado["total"] == 0:
            return {
                "resposta": "Não encontrei veterinários cadastrados na clínica no momento.",
                "dados": resultado,
            }

        linhas = [f"Temos {resultado['total']} veterinário(s) disponível(is):\n"]
        for v in resultado["veterinarios"]:
            linhas.append(f"• {v['nome']} — {v['especialidade']}")

        linhas.append("\nGostaria de verificar horários disponíveis com algum deles?")

        return {"resposta": "\n".join(linhas), "dados": resultado}

    def _handle_ver_agendamentos(self, mensagem: str) -> dict[str, Any]:
        """Handler para: 'quais são os agendamentos de hoje?'"""
        # Detecta se pergunta amanhã ou hoje
        data = datetime.now()
        if "amanhã" in mensagem or "amanha" in mensagem:
            data = datetime.now() + timedelta(days=1)

        resultado = tools.listar_agendamentos_do_dia(self.db, self.clinica_id, data)

        if not resultado["sucesso"] or resultado["total"] == 0:
            return {
                "resposta": f"Não há agendamentos para {resultado.get('data', 'esta data')}.",
                "dados": resultado,
            }

        linhas = [f"Agendamentos do dia {resultado['data']}:\n"]
        for a in resultado["agendamentos"]:
            linhas.append(
                f"• {a['inicio']} – {a['nome_cliente']} | Pet: {a['nome_pet']} | {a['status']}"
            )

        return {"resposta": "\n".join(linhas), "dados": resultado}

    def _handle_ver_horarios(self, mensagem: str) -> dict[str, Any]:
        """Handler para: 'quais horários estão disponíveis?'"""
        # Primeiro busca os veterinários da clínica
        vets = tools.buscar_veterinarios(self.db, self.clinica_id)

        if not vets["sucesso"] or vets["total"] == 0:
            return {
                "resposta": "Não há veterinários disponíveis para verificar horários.",
                "dados": {},
            }

        # Usa o primeiro veterinário ativo para sugerir horários
        # Futuramente o LLM identificará o veterinário pelo nome na mensagem
        primeiro_vet = vets["veterinarios"][0]
        data = datetime.now() + timedelta(days=1)  # padrão: amanhã

        resultado = tools.sugerir_horarios(
            db=self.db,
            clinica_id=self.clinica_id,
            veterinario_id=primeiro_vet["id"],
            data=data,
        )

        if not resultado["sucesso"] or resultado["total_livres"] == 0:
            return {
                "resposta": f"Não há horários livres com {primeiro_vet['nome']} para amanhã.",
                "dados": resultado,
            }

        linhas = [
            f"Horários disponíveis com {primeiro_vet['nome']} "
            f"para {resultado['data']}:\n"
        ]
        # Mostra no máximo 5 sugestões para não sobrecarregar o usuário
        for slot in resultado["slots_livres"][:5]:
            linhas.append(f"• {slot['inicio']} – {slot['fim']}")

        if resultado["total_livres"] > 5:
            linhas.append(f"... e mais {resultado['total_livres'] - 5} horário(s).")

        linhas.append("\nQual horário prefere? Me informe seu nome e do seu pet!")

        # Salva no contexto para o handler de agendamento usar depois
        self.contexto["veterinario_sugerido"] = primeiro_vet
        self.contexto["data_sugerida"] = data

        return {"resposta": "\n".join(linhas), "dados": resultado}

    def _handle_agendar_consulta(self, mensagem: str) -> dict[str, Any]:
        """
        Handler para: 'quero agendar uma consulta'.

        Estado atual (MVP):
            Não temos coleta de dados via conversa ainda.
            Retornamos uma mensagem pedindo as informações
            e mostramos os horários disponíveis.

        Fase 2 (com LLM):
            O LLM extrairá nome, pet e horário da própria mensagem
            e `criar_agendamento()` será chamado diretamente.
        """
        # Por enquanto redireciona para ver horários e solicita dados
        resultado_horarios = self._handle_ver_horarios(mensagem)

        resposta_base = resultado_horarios["resposta"]
        resposta_completa = (
            "Olá! Vou te ajudar a marcar uma consulta. 🐾\n\n"
            + resposta_base
        )

        return {"resposta": resposta_completa, "dados": resultado_horarios["dados"]}

    def _handle_desconhecido(self, mensagem: str) -> dict[str, Any]:
        """Handler padrão quando não entende a intenção."""
        return {
            "resposta": (
                "Olá! Sou o Yumi, assistente da clínica veterinária. 🐾\n"
                "Posso te ajudar com:\n"
                "• Ver veterinários disponíveis\n"
                "• Verificar horários livres\n"
                "• Agendar uma consulta\n\n"
                "Como posso te ajudar?"
            ),
            "dados": {},
        }
