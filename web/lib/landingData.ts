// Canned demo data, code snippets, and content — ported from the original data.js.
// No backend; everything renders client-side.

export type Example = {
  id: string;
  tab: string;
  filename: string;
  kind: string;
  source: string;
  schema: Record<string, unknown>;
  output: Record<string, unknown>;
  note: { label: string; body: string };
  confidence: number;
};

const SCHEMA_INVOICE = {
  invoice_number: "string",
  invoice_date: "date",
  total_amount: "number",
};

export const examples: Example[] = [
  {
    id: "receipt",
    tab: "Indian receipt",
    filename: "razorpay_receipt.pdf",
    kind: "PDF · 1 page",
    source:
      "RAZORPAY SOFTWARE PVT LTD\n" +
      "Tax Invoice / Receipt\n" +
      "------------------------------------\n" +
      "Payment ID: pay_S6lDhbqEbjQ6Bs\n" +
      "Payment Date: 26-05-2025\n" +
      "Course Fee: Rs. 1000\n" +
      "Status: CAPTURED\n" +
      "Thank you for your payment.",
    schema: SCHEMA_INVOICE,
    output: {
      invoice_number: "pay_S6lDhbqEbjQ6Bs",
      invoice_date: "2025-05-26",
      total_amount: 1000.0,
    },
    note: {
      label: "Deterministic date repair",
      body: "A model reading “26-05-2025” alone can emit the year 2605. docapi repairs dates in code — DD-MM-YYYY is normalized to ISO 2025-05-26, deterministically.",
    },
    confidence: 0.98,
  },
  {
    id: "invoice",
    tab: "Invoice",
    filename: "invoice_2043.pdf",
    kind: "PDF · 1 page",
    source:
      "NORTHWIND TRADERS\n" +
      "------------------------------------\n" +
      "Invoice #: INV-2043\n" +
      "Date: 05/18/2026\n" +
      "Bill to: Acme Robotics\n" +
      "Line items ............ 1\n" +
      "Total due: $1,280.00",
    schema: SCHEMA_INVOICE,
    output: {
      invoice_number: "INV-2043",
      invoice_date: "2026-05-18",
      total_amount: 1280.0,
    },
    note: {
      label: "Currency + locale normalization",
      body: "“$1,280.00” is parsed to the number 1280.0 and US MM/DD/YYYY is normalized to ISO — no thousands separators, no currency glyphs leaking into your JSON.",
    },
    confidence: 0.99,
  },
  {
    id: "resume",
    tab: "Résumé",
    filename: "jane_doe_resume.pdf",
    kind: "PDF · 2 pages",
    source:
      "Jane Doe\n" +
      "jane.doe@example.com\n" +
      "------------------------------------\n" +
      "Senior backend engineer, 8 years of experience.\n" +
      "Skills: Python, Go, PostgreSQL, Kubernetes, gRPC\n" +
      "\n" +
      "EXPERIENCE\n" +
      "Globex Corp — Staff Engineer\n" +
      "Initech — Senior Engineer",
    schema: {
      full_name: "string",
      email: "string",
      years_experience: "integer",
      skills: ["string"],
      experience: [{ company: "string", title: "string" }],
    },
    output: {
      full_name: "Jane Doe",
      email: "jane.doe@example.com",
      years_experience: 8,
      skills: ["Python", "Go", "PostgreSQL", "Kubernetes", "gRPC"],
      experience: [
        { company: "Globex Corp", title: "Staff Engineer" },
        { company: "Initech", title: "Senior Engineer" },
      ],
    },
    note: {
      label: "Lists, nesting & inference",
      body: "“8 years of experience” is inferred to years_experience: 8, skills become a typed array, and roles map into a nested array of objects — every value still verified against the source text.",
    },
    confidence: 0.95,
  },
];

export const reliability = [
  {
    n: "01",
    title: "Schema validation",
    body: "Every response is checked against the exact schema you sent. Wrong shape, wrong type, missing field — it never reaches your agent as “probably fine.”",
  },
  {
    n: "02",
    title: "Grounding check",
    body: "Each extracted string is verified to actually appear in the source text. Hallucinated values get flagged and confidence drops — silently-wrong data has nowhere to hide.",
  },
  {
    n: "03",
    title: "Long-document chunking",
    body: "Big docs are split into overlapping windows, extracted, then merged. No silent truncation at the context limit, no quietly dropped pages.",
  },
  {
    n: "04",
    title: "Deterministic date repair",
    body: "Dates are normalized to ISO in code, not by the model. The 26-05-2025 → year-2605 class of bug simply can’t happen.",
  },
  {
    n: "05",
    title: "One corrective retry",
    body: "If validation fails, docapi feeds the precise error back once and retries. If it still can’t comply, you get a structured error — never a guess.",
  },
  {
    n: "06",
    title: "Confidence + structured errors",
    body: "Successful calls carry a confidence signal and grounding warnings. Failures return a typed, machine-readable error your agent can branch on.",
  },
];

export type Snippet = { key: string; label: string; lang: string; code: string };

export const snippets: Snippet[] = [
  {
    key: "rest",
    label: "REST",
    lang: "bash",
    code:
      "curl -X POST https://api.docapi.dev/v1/extract \\\n" +
      "  -F 'file=@razorpay_receipt.pdf' \\\n" +
      "  -F 'schema={\"invoice_number\":\"string\",\n" +
      "             \"invoice_date\":\"date\",\n" +
      "             \"total_amount\":\"number\"}'\n" +
      "\n" +
      "# → 200 OK\n" +
      '# { "data": { ... }, "confidence": 0.98, "warnings": [] }',
  },
  {
    key: "mcp",
    label: "MCP",
    lang: "json",
    code:
      "// claude_desktop_config.json\n" +
      "{\n" +
      '  "mcpServers": {\n' +
      '    "docapi": {\n' +
      '      "command": "docapi",\n' +
      '      "args": ["mcp"],\n' +
      '      "env": { "DOCAPI_MODEL": "ollama:llama3.1" }\n' +
      "    }\n" +
      "  }\n" +
      "}\n" +
      "\n" +
      "// Registers the extract_document tool. Agents call it directly.",
  },
  {
    key: "python",
    label: "Python",
    lang: "python",
    code:
      "from docapi import extract_to_schema\n" +
      "\n" +
      "result = extract_to_schema(\n" +
      '    file="razorpay_receipt.pdf",\n' +
      "    schema={\n" +
      '        "invoice_number": str,\n' +
      '        "invoice_date": "date",\n' +
      '        "total_amount": float,\n' +
      "    },\n" +
      ")\n" +
      "\n" +
      "result.data        # {'invoice_number': 'pay_S6lDhbqEbjQ6Bs', ...}\n" +
      "result.confidence  # 0.98\n" +
      "result.warnings    # []",
  },
];

export const GITHUB = "https://github.com/Waterbottles792/docapi";
