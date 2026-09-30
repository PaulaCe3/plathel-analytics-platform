"""Incremental Excel-compatible CSV serialization, never an export file on disk."""
import csv
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from analytics_core.exports.security import safe_cell, unique_headers


class CSVExporter:
    format = "csv"
    content_type = "text/csv; charset=utf-8"

    def export(self, source, options):
        delimiter, decimal = (";", ",") if source.locale.lower().startswith("es") else (",", ".")
        buffer = StringIO(newline="")
        writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n")
        def serialize(values):
            serialized = []
            for value in values:
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                elif isinstance(value, (float, Decimal)):
                    value = str(value).replace(".", decimal)
                else:
                    value = safe_cell(value)
                serialized.append(value)
            writer.writerow(serialized)
            chunk = buffer.getvalue().encode("utf-8")
            buffer.seek(0)
            buffer.truncate(0)
            return chunk
        yield b"\xef\xbb\xbf" + serialize(unique_headers([safe_cell(header) for header in source.headers]))
        for row in source.rows():
            yield serialize(row)
