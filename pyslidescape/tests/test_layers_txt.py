import pyslidescape


def test_minimal():
    layers = pyslidescape.layers_txt.loads("a,b,c")
    assert "a,b,c" in layers
    speech = layers["a,b,c"]
    assert len(speech) == 0
    dump = pyslidescape.layers_txt.dumps(layers)
    assert dump == "a,b,c\n"


def test_small():
    layers = pyslidescape.layers_txt.loads(
        "a,b,c\n    Foo\n    Bar\na,b,d\n    Nom\n"
    )
    assert "a,b,c" in layers
    speech = layers["a,b,c"]
    assert len(speech) == 2
    speech[0] == "Foo"
    speech[1] == "Bar"

    assert "a,b,d" in layers
    speech = layers["a,b,d"]
    assert len(speech) == 1
    speech[0] == "Nom"
