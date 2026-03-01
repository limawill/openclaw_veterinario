from yumi.utils.tools import Tools


def test_remove_espaco_string():
    # Testa remoção de espaços em branco
    assert Tools.remove_espaco_string("  abc123  ") == "abc123"
    assert Tools.remove_espaco_string("   ") == ""
    assert Tools.remove_espaco_string("no_spaces") == "no_spaces"
    assert Tools.remove_espaco_string("") == ""
