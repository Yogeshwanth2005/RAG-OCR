from ocrrag.script import char_class, script_of

def test_classes():
    assert char_class("క") == "consonant" and char_class("ా") == "matra"
    assert char_class("్") == "virama" and char_class("ం") == "modifier"
    assert char_class("త") == "consonant" and char_class("்") == "virama"
    assert char_class("ௗ") == "matra" and char_class("ஃ") == "vowel"
    assert char_class("‍") == "joiner" and char_class("a") == "other"

def test_script_of():
    assert script_of("క") == "te" and script_of("த") == "ta" and script_of("1") is None
