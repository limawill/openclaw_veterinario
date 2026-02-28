"""
Módulo centralizado de logging com boas práticas.

Fornece um logger configurado com:
- Formato padronizado: DATA:HORA - NÍVEL - MENSAGEM - ARQUIVO - FUNÇÃO/CLASSE
- Saída em console e arquivo com rotação
- Níveis de severidade apropriados
- Não expõe dados sensíveis
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from yumi.core.config import settings

# Criar diretório de logs se não existir
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Nome do arquivo de log com data
log_filename = LOGS_DIR / f"yumi_{datetime.now().strftime('%Y%m%d')}.log"


class CustomFormatter(logging.Formatter):
    """Formatter personalizado com cores no console e formato estruturado."""
    
    # Cores ANSI para diferentes níveis
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m'        # Reset
    }
    
    FORMAT_CONSOLE = (
        "%(asctime)s - %(levelname)s - %(message)s - "
        "%(filename)s - %(funcName)s"
    )
    
    FORMAT_FILE = (
        "%(asctime)s - %(levelname)s - %(message)s - "
        "%(filename)s - %(funcName)s - %(pathname)s:%(lineno)d"
    )
    
    def __init__(self, use_color=False):
        super().__init__()
        self.use_color = use_color
    
    def format(self, record):
        if self.use_color:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}"
                    f"{levelname}"
                    f"{self.COLORS['RESET']}"
                )
            self._style._fmt = self.FORMAT_CONSOLE
        else:
            self._style._fmt = self.FORMAT_FILE
        
        # Data no formato especificado
        record.asctime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return super().format(record)


def setup_logger(name: str = "yumi") -> logging.Logger:
    """
    Configura e retorna um logger centralizado.
    
    Args:
        name: Nome do logger (padrão: "yumi")
    
    Returns:
        logging.Logger: Logger configurado
    
    Exemplo:
        >>> logger = setup_logger()
        >>> logger.info("Aplicação iniciada")
        >>> logger.error("Erro ao conectar ao banco", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Evitar handlers duplicados
    if logger.handlers:
        return logger
    
    # Definir nível baseado na configuração
    log_level = (
        logging.DEBUG 
        if settings.ENVIRONMENT == "development" 
        else logging.INFO
    )
    logger.setLevel(log_level)
    
    # =====================================================
    # HANDLER - CONSOLE
    # =====================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = CustomFormatter(use_color=True)
    console_handler.setFormatter(console_formatter)
    
    # =====================================================
    # HANDLER - ARQUIVO COM ROTAÇÃO
    # =====================================================
    # RotatingFileHandler: cria novo arquivo quando atinge tamanho limite
    # maxBytes: 10MB, backupCount: mantém 5 arquivos antigos
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_filename,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = CustomFormatter(use_color=False)
    file_handler.setFormatter(file_formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log de inicialização
    logger.info(
        f"Logger inicializado - Ambiente: {settings.ENVIRONMENT} - "
        f"Arquivo: {log_filename}"
    )
    
    return logger


# Criar instância global do logger
logger = setup_logger()


# Aliases para uso mais simples
def log_info(message: str, **kwargs):
    """Registra mensagem de informação."""
    logger.info(message, **kwargs)


def log_error(message: str, exception=None, **kwargs):
    """Registra mensagem de erro."""
    if exception:
        logger.error(message, exc_info=True, **kwargs)
    else:
        logger.error(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Registra mensagem de aviso."""
    logger.warning(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Registra mensagem de debug."""
    logger.debug(message, **kwargs)


def log_critical(message: str, exception=None, **kwargs):
    """Registra mensagem crítica."""
    if exception:
        logger.critical(message, exc_info=True, **kwargs)
    else:
        logger.critical(message, **kwargs)
