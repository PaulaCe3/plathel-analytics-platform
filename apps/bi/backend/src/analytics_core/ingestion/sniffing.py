"""CSV encoding and dialect detection."""

import csv
from pathlib import Path

from charset_normalizer import from_bytes

from analytics_core.errors import AppError

DELIMITERS = ",;\t|"


def detect_encoding(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            pass
    match = from_bytes(data).best()
    if match and match.encoding:
        candidate = match.encoding.lower()
        if candidate in {"cp1252", "windows-1252", "latin_1", "latin-1", "iso8859_1"}:
            return "cp1252" if "1252" in candidate else "latin-1"
    for encoding in ("cp1252", "latin-1"):
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            pass
    raise AppError(code="ENCODING_UNDETECTED", http_status=422, message="No se pudo detectar la codificación del CSV.")


def detect_delimiter(text: str) -> str:
    sample = "\n".join(line for line in text.splitlines()[:30] if line.strip())
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        scores: dict[str, tuple[int, int]] = {}
        for delimiter in DELIMITERS:
            widths = [len(row) for row in csv.reader(sample.splitlines(), delimiter=delimiter)]
            useful = [width for width in widths if width > 1]
            scores[delimiter] = (len(useful), max(useful, default=1))
        delimiter, score = max(scores.items(), key=lambda item: item[1])
        if score[0] == 0:
            raise AppError(code="HEADER_NOT_FOUND", http_status=422, message="No se pudo detectar el delimitador del CSV.")
        return delimiter


def sniff_csv(path: Path, encoding: str | None = None, delimiter: str | None = None) -> tuple[str, str]:
    sample = path.read_bytes()[:128_000]
    if b"\x00" in sample:
        raise AppError(code="FILE_CORRUPT", http_status=422, message="El CSV contiene bytes no válidos.")
    resolved_encoding = encoding or detect_encoding(sample)
    text = sample.decode(resolved_encoding)
    return resolved_encoding, delimiter or detect_delimiter(text)
