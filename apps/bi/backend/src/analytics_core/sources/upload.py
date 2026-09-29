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
    ) -> tuple[str, int]:
        extension = validate_extension(filename, allowed_extensions)
        destination.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with destination.open("wb") as target:
            while chunk := stream.read(self.chunk_size):
                size += len(chunk)
                if size > max_bytes:
                    raise AppError(code="FILE_TOO_LARGE", http_status=413, message="El archivo supera el tamaño máximo permitido.")
                target.write(chunk)
        if size == 0:
            raise AppError(code="FILE_EMPTY", http_status=422, message="El archivo está vacío.")
        if extension == ".csv":
            if b"\x00" in destination.read_bytes()[:128_000]:
                raise AppError(code="FILE_CORRUPT", http_status=422, message="El CSV contiene bytes no válidos.")
        else:
            validate_xlsx(destination, max_bytes * 20)
        return extension, size
