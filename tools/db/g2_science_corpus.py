"""
Grade 2 Science curriculum ingest targets.

Unit 1 teacher guide (Google Doc):
https://docs.google.com/document/d/1SNRc-NFiJy41Jxrko8nZ158Od4gJxy1cojiNzEeOvXM/edit

Each ``unit_id`` uses ``Science_2_U{number}_{doc_id_prefix}`` where ``doc_id_prefix`` is the
first eight characters of the Google Doc file id (same convention as ``g2_math_corpus``).

SSOT for Doc ids: ``reference_docs/scraped_registry.json`` -> ``Grade 2`` -> ``Science``.

## Reference mirror (same hierarchical scraper as Math / ELA)

From repo root, with OAuth in ``tools/scraper/credentials/``:

  python tools/scraper/main.py 1SNRc-NFiJy41Jxrko8nZ158Od4gJxy1cojiNzEeOvXM ^
    --out reference_docs/scraped --depth 3 --force

The root folder name comes from the live Doc title (e.g. ``Copy_of__2nd_Grade_Science``).
Main export artifacts:

  reference_docs/scraped/<DocTitleSanitized>/originals/<DocTitleSanitized>.docx
  reference_docs/scraped/<DocTitleSanitized>/originals/<DocTitleSanitized>.json

Very large guides: set ``GOOGLE_API_HTTP_TIMEOUT_SEC=600`` (see ``tools/scraper/docs_client.py``).

Offline DB ingest for this unit (optional ``--docx`` pointing at the scraped .docx):

  python tools/db/ingest_wave_unit.py --db path/to/curriculum.db --unit-id Science_2_U1_1SNRc-NF --grade 2 ^
    --subject Science --unit-number 1 --title "Grade 2 Science Unit 1: Matter" ^
    --doc-id 1SNRc-NFiJy41Jxrko8nZ158Od4gJxy1cojiNzEeOvXM ^
    --docx "reference_docs/scraped/Copy_of__2nd_Grade_Science/originals/Copy_of__2nd_Grade_Science.docx"

The ingest above creates **one** unit and **~65** parser lesson rows (full-grade compendium). To match
the **writer curriculum** (**6 modules**, **20 lessons**, irregular day bands preserved in Science JSON),
run canonicalization **with no other process locking** ``curriculum.db`` (stop the API first):

  python tools/db/canonicalize_g2_science_modules.py --db path/to/curriculum.db

Or in one step after a fresh monolithic ingest:

  python tools/db/ingest_wave_unit.py ...same args... --canonicalize-g2-science-modules

Canonical shape is SSOT in ``tools/db/g2_science_canonical_ssot.py`` (maps parser row numbers 1..65 into
20 lessons; row 9 skipped as duplicate Solids).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class G2ScienceUnitSpec:
    registry_key: str
    doc_id: str
    unit_id: str
    unit_number: int
    title: str


G2_SCIENCE_UNITS: Tuple[G2ScienceUnitSpec, ...] = (
    G2ScienceUnitSpec(
        registry_key="Unit_1_Matter",
        doc_id="1SNRc-NFiJy41Jxrko8nZ158Od4gJxy1cojiNzEeOvXM",
        unit_id="Science_2_U1_1SNRc-NF",
        unit_number=1,
        title="Grade 2 Science Unit 1: Matter",
    ),
)
