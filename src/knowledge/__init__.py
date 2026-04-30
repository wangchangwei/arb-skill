"""Labor law knowledge base module.

Provides legal basis lookup and evidence checklist generation
for labor arbitration cases.
"""

from src.knowledge.labor_law import (
    LegalBasis,
    lookup_legal_basis,
    get_evidence_checklist,
)

__all__ = [
    "LegalBasis",
    "lookup_legal_basis",
    "get_evidence_checklist",
]
