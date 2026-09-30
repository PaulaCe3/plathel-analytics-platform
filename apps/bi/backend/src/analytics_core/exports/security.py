"""Neutralize formula-like text while preserving typed numeric values."""

def safe_cell(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def unique_headers(headers):
    used = set()
    result = []
    for value in headers:
        base = value or "Columna"
        header, suffix = base, 2
        while header.casefold() in used:
            header = f"{base} ({suffix})"
            suffix += 1
        used.add(header.casefold())
        result.append(header)
    return tuple(result)
