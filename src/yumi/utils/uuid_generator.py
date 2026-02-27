import uuid


def gerar_uuid():
    """
        Gera um UUID único para uso como ID em tabelas do 
        banco de dados
    """
    return str(uuid.uuid4())
