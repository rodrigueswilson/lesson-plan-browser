from lxml import etree

from tools.scraper.table_extractor import (
    _join_runs_for_paragraph_text,
    _looks_like_equation_token_loss,
    _omml_node_to_text,
)


def _omml(xml: str):
    return etree.fromstring(xml.encode("utf-8"))


def test_omml_fraction_to_text():
    node = _omml(
        """
        <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
          <m:f>
            <m:num><m:r><m:t>a</m:t></m:r></m:num>
            <m:den><m:r><m:t>b</m:t></m:r></m:den>
          </m:f>
        </m:oMath>
        """
    )
    assert _omml_node_to_text(node) == "a/b"


def test_omml_sqrt_to_text():
    node = _omml(
        """
        <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
          <m:rad>
            <m:e><m:r><m:t>x</m:t></m:r></m:e>
          </m:rad>
        </m:oMath>
        """
    )
    assert _omml_node_to_text(node) == "sqrt(x)"


def test_join_runs_avoids_alnum_glue():
    runs = [{"text": "a/b"}, {"text": "as"}, {"text": "a"}, {"text": "multiple"}]
    assert _join_runs_for_paragraph_text(runs) == "a/b as a multiple"


def test_equation_loss_heuristic():
    assert _looks_like_equation_token_loss("Understand a fraction as a multiple of .")
    assert not _looks_like_equation_token_loss("Understand a fraction a/b as a multiple of 1/b.")
