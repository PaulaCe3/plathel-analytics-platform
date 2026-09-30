"""Streaming persistence of an untrusted file to an opaque path."""

from pathlib import Path
from typing import BinaryIO

from analytics_core.errors import AppError
from analytics_core.security.uploads import validate_extension, validate_xlsx


class UploadSource:
    chunk_size = 1024 * 1024

    def save(
        self,
        stream: BinaryIO,
        filename: str,
        destination: Path,
        *,
        allowed_extensions: tuple[str, ...],
        max_bytes: int,
        max_zip_entries: int = 1000,
        max_zip_expanded_bytes: int = 100 * 1024 * 1024,
        max_zip_ratio: float = 100,
    ) -> tuple[str, int]:
        extension = validate_extension(filename, allowed_extensions)
        destination.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with destination.open("wb") as target:
            while chunk := stream.read(self.chunk_size):
                size += len(chunk)
                if size > max_bytes:
                    raise AppError(code="FILE_TOO_LARGE", http_status=413, message="El archivo supera el tamaño máximo permitido.")
                if extension == ".csv" and b"\x00" in chunk:
                    raise AppError(code="FILE_CORRUPT", http_status=422, message="El CSV contiene bytes no válidos.")
                target.write(chunk)
        if size == 0:
            raise AppError(code="FILE_EMPTY", http_status=422, message="El archivo está vacío.")
        if extension == ".csv":
            with destination.open("rb") as source:
                signature = source.read(4)
            if signature.startswith((b"PK", b"MZ", b"\x7fELF")):
                raise AppError(code="FILE_CORRUPT", http_status=422, message="El CSV contiene bytes no válidos.")
        else:
            validate_xlsx(destination, max_zip_expanded_bytes, max_zip_entries, max_zip_ratio)
        return extension, size
