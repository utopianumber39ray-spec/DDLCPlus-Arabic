def reordered_csv(arabic_raw, english_raw):
    arabic_lines = arabic_raw.split("\\n")
    english_lines = english_raw.split("\\n")
    if len(arabic_lines) != len(english_lines):
        raise ValueError("CSV line structure differs")
    output = []
    changed = 0
    for line_number, (arabic, english) in enumerate(zip(arabic_lines, english_lines), 1):
        arabic_fields = arabic.split(",")
        english_fields = english.split(",")
        arabic_is_reversed = len(arabic_fields) == 4 and all(
            field.lstrip("-").isdigit() for field in arabic_fields[:3]
        )
        english_is_data = len(english_fields) == 4 and all(
            field.lstrip("-").isdigit() for field in english_fields[1:]
        )
        if english_is_data and arabic == english:
            output.append(arabic)
            continue
        if arabic_is_reversed != english_is_data:
            raise ValueError(f"CSV data/comment mismatch at line {line_number}")
        if not english_is_data:
            if bool(arabic) != bool(english):
                raise ValueError(f"blank-line mismatch at line {line_number}")
            output.append(arabic)
            continue
        if [int(field) for field in arabic_fields[:3]] != [int(field) for field in english_fields[1:]]:
            raise ValueError(f"CSV points differ at line {line_number}")
        output.append(",".join([arabic_fields[3], *arabic_fields[:3]]))
        changed += 1
    if changed != 228:
        raise ValueError(f"expected 228 reordered rows, got {changed}")
    return "\\n".join(output)
