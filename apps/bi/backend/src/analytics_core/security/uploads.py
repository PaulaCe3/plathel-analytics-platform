"""Small, explicit validation layer for untrusted uploads."""

from pathlib import Path, PurePath
from zipfile import BadZipFile, ZipFile

from analytics_core.errors import AppError


def validate_extension(filename: str, allowed: tuple[str, ...]) -> str:
    if not filename or "\x00" in filename:
        raise AppError(code="FILE_TYPE_UNSUPPORTED", http_status=415, message="El nombre del archivo no es válido.")
    name = filename.replace("\\", "/")
    if PurePath(name).name != name or name in {".", ".."}:
        raise AppError(code="FILE_TYPE_UNSUPPORTED", http_status=415, message="El nombre del archivo contiene una ruta no permitida.")
    extension = Path(name).suffix.lower()
    if extension not in allowed:
        raise AppError(code="FILE_TYPE_UNSUPPORTED", http_status=415, message="Solo se admiten archivos CSV y XLSX.")
    return extension


def validate_xlsx(path: Path, max_uncompressed_bytes: int) -> None:
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                raise AppError(code="FILE_CORRUPT", http_status=422, message="El XLSX no tiene una estructura válida.")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise AppError(code="FILE_TYPE_UNSUPPORTED", http_status=415, message="No se admiten libros con macros.")
            total = sum(item.file_size for item in archive.infolist())
            compressed = max(1, sum(item.compress_size for item in archive.infolist()))
            if total > max_uncompressed_bytes or total / compressed > 100:
                raise AppError(code="FILE_TOO_LARGE", http_status=413, message="El XLSX expandido supera el límite permitido.")
            if any("externalLink" in name for name in names):
                raise AppError(code="FILE_TYPE_UNSUPPORTED", http_status=415, message="No se admiten vínculos externos en XLSX.")
    except BadZipFile as exc:
        raise AppError(code="FILE_CORRUPT", http_status=422, message="El XLSX está dañado o no es válido.") from exc
