"use client";

import { useState } from "react";
import { snippets } from "@/lib/landingData";
import { highlightCode } from "@/lib/highlight";

export default function CodeTabs() {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);
  const snip = snippets[active];

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(snip.code);
    } catch {
      /* clipboard unavailable */
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div>
      <div className="code-tabs" role="tablist" aria-label="Integration methods">
        {snippets.map((s, i) => (
          <button
            key={s.key}
            className="code-tab"
            role="tab"
            aria-selected={i === active}
            onClick={() => setActive(i)}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div className="code-panel">
        <button
          className={`copy${copied ? " copied" : ""}`}
          type="button"
          onClick={copy}
        >
          <span aria-hidden>⧉</span> <span>{copied ? "Copied" : "Copy"}</span>
        </button>
        <pre>
          <code
            dangerouslySetInnerHTML={{ __html: highlightCode(snip.code, snip.lang) }}
          />
        </pre>
      </div>
    </div>
  );
}
