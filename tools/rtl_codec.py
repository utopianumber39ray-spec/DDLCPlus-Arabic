import re
import unicodedata

import arabic_reshaper
from bidi.algorithm import get_display

TOKEN_RE = re.compile(r"<[^>\n]+>|\[[^\]\n]+\]|'[^'\n]+'")
RESHAPER = arabic_reshaper.ArabicReshaper(
    {"support_ligatures": True, "delete_harakat": False}
)


def protect_tokens(text):
    tokens = []

    def replace(match):
        tokens.append(match.group(0))
        return chr(0x1EE00 + len(tokens) - 1)

    return TOKEN_RE.sub(replace, text), tokens


def restore_tokens(text, tokens):
    for index, token in enumerate(tokens):
        text = text.replace(chr(0x1EE00 + index), token)
    return text


def unshape_character(char):
    if 0xFB50 <= ord(char) <= 0xFEFF:
        return unicodedata.normalize("NFKC", char)
    return char


def decode_body(body):
    protected, tokens = protect_tokens(body)
    displayed = get_display(protected)
    logical = "".join(unshape_character(char) for char in displayed)
    logical = restore_tokens(logical, tokens)
    for open_tag, close_tag in (("<i>", "</i>"), ("<color=#000>", "</color>")):
        opening = body.find(open_tag)
        closing = body.find(close_tag)
        if closing >= 0 and (opening < 0 or closing < opening):
            marker = "\x00"
            logical = logical.replace(close_tag, marker).replace(open_tag, close_tag).replace(marker, open_tag)
    return logical


def encode_body(logical):
    protected, tokens = protect_tokens(logical)
    shaped = get_display(RESHAPER.reshape(protected))
    return restore_tokens(shaped, tokens)


def decode_raw(raw):
    lines = []
    for line in raw.split("\n"):
        prefix = "<align=right>" if line.startswith("<align=right>") else ""
        suffix = "</align>" if line.endswith("</align>") else ""
        if not prefix:
            lines.append(line)
            continue
        body = line[len(prefix):len(line) - len(suffix) if suffix else None]
        lines.append(decode_body(body))
    return "\n".join(lines)


def encode_raw(raw):
    lines = []
    for line in raw.split("\n"):
        prefix = "<align=right>" if line.startswith("<align=right>") else ""
        suffix = "</align>" if line.endswith("</align>") else ""
        body = line[len(prefix):len(line) - len(suffix) if suffix else None]
        lines.append(prefix + encode_body(body) + suffix)
    return "\n".join(lines)


def main():
    import UnityPy

    bundle = UnityPy.load(".work/decrypted/langar.cy.bundle")
    mono = next(obj for obj in bundle.objects if obj.type.name == "MonoBehaviour")
    entries = mono.read_typetree()["linesdict"]
    total = 0
    failures = []
    for entry in entries:
        for raw in entry["values"]:
            for line in raw.split("\n"):
                prefix = "<align=right>" if line.startswith("<align=right>") else ""
                if not prefix:
                    continue
                suffix = "</align>" if line.endswith("</align>") else ""
                body = line[len(prefix):len(line) - len(suffix) if suffix else None]
                total += 1
                logical = decode_body(body)
                rebuilt = prefix + encode_body(logical) + suffix
                if rebuilt != line:
                    if len(failures) < 12:
                        failures.append((line, logical, rebuilt))
    print(f"aligned lines={total}; failures={len(failures)}")
    for raw, logical, rebuilt in failures:
        print("RAW", repr(raw))
        print("LOGICAL", repr(logical))
        print("REBUILT", repr(rebuilt))


if __name__ == "__main__":
    main()
