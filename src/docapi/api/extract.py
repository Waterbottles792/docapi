"""POST /v1/extract — multipart upload -> schema-shaped JSON. Same pipeline as MCP (later)."""
from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from ..core.errors import DocApiError
from ..core.pipeline import extract_to_schema

router = APIRouter()


_SCHEMA_EXAMPLE = '{"invoice_number": "string", "invoice_date": "date", "total_amount": "number"}'


@router.post("/v1/extract")
async def extract_endpoint(
    file: UploadFile = File(..., description="Document to extract from (.pdf, .png, .jpg, .jpeg)"),
    schema: str = Form(
        ...,
        description=(
            "JSON object mapping field names to types: string, number, integer, boolean, "
            "date. Append ? for optional; use [ {..} ] for arrays and {..} for nested objects."
        ),
        examples=[_SCHEMA_EXAMPLE],
    ),
    options: str | None = Form(
        None,
        description='Optional JSON, e.g. {"ocr": "auto"}. Leave empty if unused.',
        examples=['{"ocr": "auto"}'],
    ),
) -> JSONResponse:
    try:
        schema_obj = json.loads(schema)
        options_obj = json.loads(options) if options else {}
    except json.JSONDecodeError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"type": "bad_request", "message": f"invalid JSON: {exc}"}},
        )

    file_bytes = await file.read()
    try:
        result = extract_to_schema(
            file_bytes, file.filename or "upload", schema_obj, options_obj
        )
    except DocApiError as exc:
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())
    except ValueError as exc:  # bad schema shape
        return JSONResponse(
            status_code=400,
            content={"error": {"type": "bad_request", "message": str(exc)}},
        )

    return JSONResponse(
        content={
            "data": result.data,
            "confidence": result.confidence,
            "pages": result.pages,
            "warnings": result.warnings,
        }
    )
