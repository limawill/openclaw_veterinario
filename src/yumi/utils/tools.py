from yumi.core.logger import logger


class Tools:
    """Classe utilitária para funções comuns."""
    
    @staticmethod
    def remove_espaco_string(id: str) -> str:
        """Remove espaços em branco do início e fim da string."""
        logger.debug(f"Removendo espaços em branco do ID: {id}")
        id_sem_espaco = id.strip()
        logger.debug(f"ID sem espaços: {id_sem_espaco}")
        return id_sem_espaco