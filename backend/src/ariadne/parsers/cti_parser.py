"""Phase 1: turns unstructured CTI text (Mandiant/CrowdStrike-style report,
already extracted from PDF/Markdown) into a structured CtiSummary.

This starting implementation is a naive regex pass — good enough for reports
that state the CVE and affected software explicitly. Swap in an
OllamaProvider.generate() extraction call (see rag/llm_providers.py) once
messier, less templated reports need parsing; keep the two paths separable
so extraction logic never blurs into the LLM reasoning step (Phase 3).
"""

import re

from ariadne.schemas import CtiSummary

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}")


def parse_cti_report(text: str, *, source_report: str) -> CtiSummary:
    cve_match = CVE_PATTERN.search(text)
    if cve_match is None:
        raise ValueError("No CVE identifier found in report; cannot build a grounded CtiSummary")

    return CtiSummary(
        cve_id=cve_match.group(0),
        target_software=_extract_field(text, "Affected Product") or "unknown",
        affected_versions=_extract_field(text, "Affected Versions") or "unknown",
        attack_vector=_extract_field(text, "Attack Vector") or "unknown",
        source_report=source_report,
    )


def _extract_field(text: str, label: str) -> str | None:
    match = re.search(rf"{re.escape(label)}:\s*(.+)", text)
    return match.group(1).strip() if match else None
