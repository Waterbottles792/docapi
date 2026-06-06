"use client";

import {
  FileJson,
  Cpu,
  Plug,
  FlaskConical,
  ShieldCheck,
  ScanText,
  KeyRound,
} from "lucide-react";
import RadialOrbitalTimeline from "@/components/ui/radial-orbital-timeline";

// docapi's real roadmap, mapped onto the orbital timeline.
const roadmap = [
  {
    id: 1,
    title: "Extract-to-schema",
    date: "Shipped",
    content: "The core pipeline: file + schema in, schema-valid JSON out, over REST.",
    category: "Core",
    icon: FileJson,
    relatedIds: [2],
    status: "completed" as const,
    energy: 100,
  },
  {
    id: 2,
    title: "Local model + dates",
    date: "Shipped",
    content: "Free local extraction via Ollama, plus deterministic date repair.",
    category: "Core",
    icon: Cpu,
    relatedIds: [1, 3],
    status: "completed" as const,
    energy: 95,
  },
  {
    id: 3,
    title: "MCP tool",
    date: "Shipped",
    content: "The extract_document tool, callable directly by agents — no HTTP glue.",
    category: "Integrate",
    icon: Plug,
    relatedIds: [2, 4],
    status: "completed" as const,
    energy: 88,
  },
  {
    id: 4,
    title: "Eval + grounding",
    date: "Shipped",
    content: "Field-level eval harness, grounding checks, and long-document chunking.",
    category: "Reliability",
    icon: FlaskConical,
    relatedIds: [3, 5],
    status: "completed" as const,
    energy: 80,
  },
  {
    id: 5,
    title: "Claude provider",
    date: "Shipped",
    content: "The paid, high-quality path — big context, fast on long documents.",
    category: "Reliability",
    icon: ShieldCheck,
    relatedIds: [4, 6],
    status: "completed" as const,
    energy: 72,
  },
  {
    id: 6,
    title: "OCR fallback",
    date: "Next",
    content: "Text extraction for scanned PDFs and image documents.",
    category: "Roadmap",
    icon: ScanText,
    relatedIds: [5, 7],
    status: "pending" as const,
    energy: 35,
  },
  {
    id: 7,
    title: "Hosted docapi",
    date: "In progress",
    content: "Auth, usage metering, and deploy — an API key instead of a local model.",
    category: "Roadmap",
    icon: KeyRound,
    relatedIds: [6],
    status: "in-progress" as const,
    energy: 50,
  },
];

export default function Roadmap() {
  return <RadialOrbitalTimeline timelineData={roadmap} />;
}
