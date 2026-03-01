from yumi.utils.uuid_generator import gerar_uuid


def test_gerar_uuid():
    # Testa se o UUID gerado é uma string e tem o formato correto
    uuid1 = gerar_uuid()
    uuid2 = gerar_uuid()
    
    assert isinstance(uuid1, str)
    assert isinstance(uuid2, str)
    assert len(uuid1) == 36  # Formato padrão do UUID
    assert len(uuid2) == 36
    assert uuid1 != uuid2  # Deve gerar UUIDs únicos