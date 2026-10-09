"""Minimale S-expression parser/serializer voor KiCad bestanden.

Lijsten worden Python lists, quoted strings worden QStr, atomen gewone str.
Getallen blijven tekst zodat er nooit afrondingsfouten ontstaan.
"""


class QStr(str):
    """Een string die tussen aanhalingstekens geschreven moet worden."""


def parse(text):
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c in " \t\r\n":
            pos += 1
        elif c == "(":
            stack.append([])
            pos += 1
        elif c == ")":
            if len(stack) < 2:
                raise ValueError("Onverwachte ')' op positie %d" % pos)
            lst = stack.pop()
            stack[-1].append(lst)
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while pos < n and text[pos] != '"':
                if text[pos] == "\\" and pos + 1 < n:
                    nxt = text[pos + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
                    pos += 2
                else:
                    buf.append(text[pos])
                    pos += 1
            pos += 1
            stack[-1].append(QStr("".join(buf)))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()"':
                pos += 1
            stack[-1].append(text[start:pos])
    if len(stack) != 1:
        raise ValueError("Niet-gesloten haakjes")
    return stack[0][0] if len(stack[0]) == 1 else stack[0]


def _atom(x):
    if isinstance(x, QStr):
        s = x.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return '"%s"' % s
    return str(x)


def dumps(node, indent=0):
    if not isinstance(node, list):
        return _atom(node)
    pad = "  " * indent
    if all(not isinstance(x, list) for x in node):
        return pad + "(" + " ".join(_atom(x) for x in node) + ")"
    out = []
    head = []
    i = 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(_atom(node[i]))
        i += 1
    out.append(pad + "(" + " ".join(head))
    for child in node[i:]:
        if isinstance(child, list):
            out.append(dumps(child, indent + 1))
        else:
            out.append("  " * (indent + 1) + _atom(child))
    out.append(pad + ")")
    return "\n".join(out)


# --- hulpfuncties ---------------------------------------------------------

def tag(node):
    return node[0] if isinstance(node, list) and node else None


def find(node, name):
    for child in node:
        if isinstance(child, list) and child and child[0] == name:
            return child
    return None


def find_all(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def walk(node):
    """Alle sub-lijsten recursief."""
    if isinstance(node, list):
        yield node
        for c in node:
            yield from walk(c)


def get_property(symbol, key):
    for p in find_all(symbol, "property"):
        if len(p) > 2 and p[1].lower() == key.lower():
            return p
    return None


def set_property(symbol, key, value, hidden=True):
    p = get_property(symbol, key)
    if p is not None:
        p[2] = QStr(value)
        return p
    prop = ["property", QStr(key), QStr(value), ["at", "0", "0", "0"],
            ["effects", ["font", ["size", "1.27", "1.27"]]] + ([["hide", "yes"]] if hidden else [])]
    # na de laatste bestaande property invoegen
    idx = max([i for i, c in enumerate(symbol) if tag(c) == "property"] or [1])
    symbol.insert(idx + 1, prop)
    return prop
