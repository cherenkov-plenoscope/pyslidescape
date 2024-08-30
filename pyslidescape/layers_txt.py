def dumps(layers, indent=4):
    out = ""
    for layers_shown_set in layers:
        out += layers_shown_set + "\n"
        for speech_line in layers[layers_shown_set]:
            out += " " * indent + speech_line + "\n"
    return out


def loads(s):
    layers = {}
    current_layer = None
    for line in str.splitlines(s):
        if len(line) > 0:
            first_char = line[0]
            if str.isspace(first_char):
                assert (
                    current_layer is not None
                ), "Expected layer before speech."
                layers[current_layer].append(str.strip(line))
            else:
                current_layer = line
                layers[current_layer] = []
    return layers


def split_show_layers_set(line):
    return str.split(line, ",")
