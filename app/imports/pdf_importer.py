"""Parse PDF files with pdfplumber, extracting tables as detected sections."""
from __future__ import annotations

import io

from app.imports.mapping_detector import detect_column_mapping, is_sample_content, score_row
from app.imports.spreadsheet_importer import _rows_to_detected_section
from app.schemas.imports import DetectedSection


def parse_pdf(file_bytes: bytes) -> list[DetectedSection]:
    try:
        import pdfplumber
    except ImportError:
        return []

    sections: list[DetectedSection] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                # First row is assumed headers
                raw_headers = [str(c).strip() if c else f"col_{i}" for i, c in enumerate(table[0])]
                col_map = detect_column_mapping(raw_headers)

                rows_as_dicts: list[dict] = []
                for row in table[1:]:
                    rows_as_dicts.append(
                        {raw_headers[i]: row[i] for i in range(min(len(raw_headers), len(row)))}
                    )

                if not rows_as_dicts:
                    continue

                sheet_name = f"Page {page_num + 1} Table {table_idx + 1}"
                section = _rows_to_detected_section(rows_as_dicts, raw_headers, sheet_name, col_map)
                sections.append(section)

    return sections
