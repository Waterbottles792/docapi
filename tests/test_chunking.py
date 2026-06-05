"""Long-document chunking: splitting, field-by-field merge, and the chunked pipeline path."""
from __future__ import annotations

from io import BytesIO

from docapi.core.chunking import CHUNK_CHARS, merge_partials, split_text
from docapi.core.pipeline import extract_to_schema
from docapi.core.schema import build_model


def test_split_keeps_windows_under_budget() -> None:
    text = "\n".join(f"line {i} " + "x" * 50 for i in range(200))
    chunks = split_text(text, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c) <= 500 or "\n" not in c for c in chunks)
    # No content lost: every original line survives somewhere.
    assert sum(c.count("line ") for c in chunks) == 200


def test_split_never_splits_a_line() -> None:
    long_line = "y" * 1000
    chunks = split_text(f"short\n{long_line}\nshort", max_chars=100)
    assert long_line in chunks  # the oversized line stays intact in its own window


def test_short_text_is_one_chunk() -> None:
    assert split_text("just a little text") == ["just a little text"]


def _model(schema: dict):
    return build_model("T", schema)


def test_merge_first_non_empty_scalar_wins() -> None:
    model = _model({"name": "string"})
    merged = merge_partials([{"name": None}, {"name": "ACME"}, {"name": "Other"}], model)
    assert merged["name"] == "ACME"


def test_merge_boolean_is_ored_across_windows() -> None:
    model = _model({"has_burger": "boolean"})
    # Only the window that saw the burger reports True; the rest are null/False.
    merged = merge_partials(
        [{"has_burger": None}, {"has_burger": False}, {"has_burger": True}], model
    )
    assert merged["has_burger"] is True


def test_merge_boolean_all_false() -> None:
    model = _model({"has_burger": "boolean"})
    merged = merge_partials([{"has_burger": False}, {"has_burger": None}], model)
    assert merged["has_burger"] is False


def test_merge_lists_union_and_dedupe() -> None:
    model = _model({"tags": ["string"]})
    merged = merge_partials(
        [{"tags": ["a", "b"]}, {"tags": ["B", "c"]}, {"tags": None}], model
    )
    assert merged["tags"] == ["a", "b", "c"]  # case-insensitive dedupe, order preserved


def test_merge_list_of_objects_unions() -> None:
    model = _model({"rows": [{"name": "string", "qty": "integer"}]})
    merged = merge_partials(
        [
            {"rows": [{"name": "x", "qty": 1}]},
            {"rows": [{"name": "y", "qty": 2}]},
            {"rows": [{"name": "x", "qty": 1}]},  # duplicate dropped
        ],
        model,
    )
    assert merged["rows"] == [{"name": "x", "qty": 1}, {"name": "y", "qty": 2}]


def test_merge_nested_object_recurses() -> None:
    model = _model({"info": {"city": "string", "zip": "string"}})
    merged = merge_partials(
        [{"info": {"city": "Pune", "zip": None}}, {"info": {"city": None, "zip": "411001"}}],
        model,
    )
    assert merged["info"] == {"city": "Pune", "zip": "411001"}


def test_merge_required_list_defaults_to_empty() -> None:
    # No window found the field -> empty list, not None (which would fail strict validation).
    model = _model({"toppings": ["string"]})
    merged = merge_partials([{"toppings": None}, {"toppings": None}], model)
    assert merged["toppings"] == []


def test_merge_required_bool_defaults_to_false() -> None:
    model = _model({"flag": "boolean"})
    merged = merge_partials([{"flag": None}], model)
    assert merged["flag"] is False


def test_make_all_optional_keeps_booleans_required() -> None:
    from docapi.core.schema import make_all_optional

    relaxed = make_all_optional(_model({"name": "string", "flag": "boolean"}))
    assert relaxed.model_fields["name"].is_required() is False
    # A boolean is total — it stays required so a window must commit true/false.
    assert relaxed.model_fields["flag"].is_required() is True


class _ByWindowUnderstander:
    """Returns a different canned dict per call, so we can simulate facts spread across pages."""

    def __init__(self, responses: list[dict]) -> None:
        self._responses = responses
        self._i = 0

    def understand(self, content, model, feedback=None):  # noqa: ANN001
        resp = self._responses[min(self._i, len(self._responses) - 1)]
        self._i += 1
        return dict(resp)


def _big_pdf(text: str) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    cv = canvas.Canvas(buf, pagesize=letter)
    for page_text in text.split("\f"):
        y = 740
        for line in page_text.split("\n"):
            cv.drawString(72, y, line[:110])
            y -= 14
        cv.showPage()
    cv.save()
    return buf.getvalue()


def test_pipeline_chunks_long_doc_and_merges_facts() -> None:
    # A document long enough to force chunking, with the "burger" fact buried on a late page.
    filler = "\n".join("This guide covers many restaurants in town." for _ in range(40))
    body = filler + "\nThe diner serves a famous burger.\n" + filler
    assert len(body) > CHUNK_CHARS
    schema = {"has_burger": "boolean", "cuisine": "string?"}

    # Simulate per-window extraction: required booleans are always committed (the
    # structured-output schema forbids null), and only the late window sees the burger.
    understander = _ByWindowUnderstander(
        [
            {"has_burger": False, "cuisine": None},
            {"has_burger": True, "cuisine": "American"},
            {"has_burger": False, "cuisine": None},
        ]
    )
    result = extract_to_schema(
        _big_pdf(body), "guide.pdf", schema, understander=understander
    )
    assert result.data["has_burger"] is True
    assert result.data["cuisine"] == "American"
    assert any("chunked" in w for w in result.warnings)
