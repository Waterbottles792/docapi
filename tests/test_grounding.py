"""Grounding check: fabricated string values are flagged; real ones pass."""
from __future__ import annotations

from docapi.core.grounding import find_ungrounded
from docapi.core.pipeline import extract_to_schema
from docapi.core.schema import build_model
from docapi.core.understand import StubUnderstander

SOURCE = (
    "ACME Bistro — famous for wood-fired pizza with mushroom and basil toppings. "
    "Opened 2019. Contact jane@acme.test. Rating 4.6."
)


def _model(schema: dict):
    return build_model("T", schema)


def test_grounded_strings_pass() -> None:
    schema = {"name": "string", "email": "string"}
    data = {"name": "ACME Bistro", "email": "jane@acme.test"}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_case_and_whitespace_insensitive() -> None:
    schema = {"name": "string"}
    data = {"name": "acme   BISTRO"}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_fabricated_string_is_flagged() -> None:
    schema = {"cuisine": "string"}
    data = {"cuisine": "Sushi"}  # not in source
    assert find_ungrounded(data, _model(schema), SOURCE) == ["cuisine"]


def test_dates_are_skipped() -> None:
    # Reformatted ISO date won't appear verbatim in the source, but must not be flagged.
    schema = {"opened": "date"}
    data = {"opened": "2019-01-01"}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_numbers_are_skipped() -> None:
    schema = {"rating": "number"}
    data = {"rating": 4.6}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_list_of_strings_paths() -> None:
    schema = {"toppings": ["string"]}
    data = {"toppings": ["mushroom", "pineapple", "basil"]}  # pineapple fabricated
    assert find_ungrounded(data, _model(schema), SOURCE) == ["toppings[1]"]


def test_nested_objects_and_lists() -> None:
    schema = {"places": [{"name": "string", "dish": "string"}]}
    data = {"places": [{"name": "ACME Bistro", "dish": "ramen"}]}
    assert find_ungrounded(data, _model(schema), SOURCE) == ["places[0].dish"]


def test_optional_string_none_is_ignored() -> None:
    schema = {"name": "string", "phone": "string?"}
    data = {"name": "ACME Bistro", "phone": None}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_empty_string_is_ignored() -> None:
    schema = {"note": "string"}
    data = {"note": "   "}
    assert find_ungrounded(data, _model(schema), SOURCE) == []


def test_pipeline_warns_and_lowers_confidence_on_hallucination() -> None:
    schema = {"name": "string", "cuisine": "string"}
    # "name" is grounded; "cuisine" is invented.
    stub = StubUnderstander({"name": "ACME Bistro", "cuisine": "Sushi"})
    pdf = _pdf(SOURCE)
    result = extract_to_schema(pdf, "doc.pdf", schema, understander=stub)
    assert any("ungrounded_fields" in w and "cuisine" in w for w in result.warnings)
    assert result.confidence <= 0.75


def test_pipeline_grounding_can_be_disabled() -> None:
    schema = {"cuisine": "string"}
    stub = StubUnderstander({"cuisine": "Sushi"})
    result = extract_to_schema(
        _pdf(SOURCE), "doc.pdf", schema, options={"grounding": "off"}, understander=stub
    )
    assert not any("ungrounded" in w for w in result.warnings)


def _pdf(text: str) -> bytes:
    from io import BytesIO

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    cv = canvas.Canvas(buf, pagesize=letter)
    y = 740
    for line in text.split(". "):
        cv.drawString(72, y, line)
        y -= 18
    cv.showPage()
    cv.save()
    return buf.getvalue()
