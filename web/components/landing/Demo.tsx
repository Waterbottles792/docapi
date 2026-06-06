"use client";

import { useEffect, useRef, useState } from "react";
import { examples } from "@/lib/landingData";
import { highlightJSON, renderSchema, renderSource } from "@/lib/highlight";

type TickState = "idle" | "active" | "done";

const TICKS = [
  { n: "01", name: "Ingest" },
  { n: "02", name: "Extract text" },
  { n: "03", name: "Understand", paid: true },
  { n: "04", name: "Validate", retry: true },
  { n: "05", name: "Normalize" },
  { n: "06", name: "Ground + score" },
];

export default function Demo() {
  const [idx, setIdx] = useState(0);
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [states, setStates] = useState<TickState[]>(() =>
    TICKS.map(() => "idle"),
  );
  const [retryShown, setRetryShown] = useState(false);
  const [confWidth, setConfWidth] = useState(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const ex = examples[idx];

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };
  useEffect(() => clearTimers, []);

  const reset = () => {
    clearTimers();
    setPhase("idle");
    setStates(TICKS.map(() => "idle"));
    setRetryShown(false);
    setConfWidth(0);
  };

  const select = (i: number) => {
    setIdx(i);
    reset();
  };

  const run = () => {
    if (phase === "running") return;
    clearTimers();
    setRetryShown(false);
    setConfWidth(0);
    setPhase("running");
    setStates(TICKS.map(() => "idle"));

    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const stepMs = reduce ? 60 : 520;

    TICKS.forEach((_, i) => {
      timers.current.push(
        setTimeout(() => {
          setStates((prev) => {
            const next = [...prev];
            if (i > 0) next[i - 1] = "done";
            next[i] = "active";
            return next;
          });
          if (i === 3 && !reduce) {
            timers.current.push(
              setTimeout(() => setRetryShown(true), stepMs * 0.35),
            );
          }
        }, stepMs * i),
      );
    });

    // finish
    timers.current.push(
      setTimeout(() => {
        setStates((prev) => {
          const next = [...prev];
          next[next.length - 1] = "done";
          return next;
        });
        setPhase("done");
        const conf = examples[idx].confidence;
        timers.current.push(
          setTimeout(() => setConfWidth(Math.round(conf * 100)), 40),
        );
      }, stepMs * TICKS.length),
    );
  };

  const running = phase === "running";

  return (
    <>
      <div className="demo-tabs" role="tablist" aria-label="Example documents">
        {examples.map((e, i) => (
          <button
            key={e.id}
            className="demo-tab"
            role="tab"
            aria-selected={i === idx}
            onClick={() => select(i)}
          >
            <span className="fdot" />
            {e.tab}
          </button>
        ))}
      </div>

      <div className="demo-grid" role="tabpanel">
        {/* INPUT column */}
        <div>
          <div className="panel">
            <div className="panel-head">
              <span>{ex.filename}</span>
              <span className="tag">{ex.kind}</span>
            </div>
            <div className="panel-body">
              <div
                className="source-doc"
                dangerouslySetInnerHTML={{ __html: renderSource(ex.source) }}
              />
            </div>
          </div>

          <div className="panel" style={{ marginTop: 18 }}>
            <div className="panel-head">
              <span>schema you ask for</span>
              <span className="tag">request</span>
            </div>
            <div className="panel-body">
              <pre
                className="code"
                dangerouslySetInnerHTML={{ __html: renderSchema(ex.schema) }}
              />
            </div>
          </div>
        </div>

        {/* OUTPUT column */}
        <div className="output-col">
          <button className="run-btn" onClick={run} disabled={running}>
            <span aria-hidden>▶</span>
            <span>{running ? "Extracting…" : phase === "done" ? "Run again" : "Run extraction"}</span>
          </button>

          {/* pipeline ticker */}
          <div className="ticker" aria-label="Extraction pipeline">
            {TICKS.map((t, i) => (
              <div
                key={t.n}
                className={`tick${t.paid ? " paid" : ""}`}
                data-state={states[i]}
              >
                {t.retry && (
                  <span className={`retry${retryShown ? " show" : ""}`}>
                    retry ↻
                  </span>
                )}
                <div className="tnum">{t.n}</div>
                <div className="tname">{t.name}</div>
                <div className="tbar">
                  <i />
                </div>
              </div>
            ))}
          </div>
          <div className="tick-cost">
            <span>
              <span className="sw" style={{ background: "var(--valid)" }} /> deterministic · free
            </span>
            <span>
              <span className="sw" style={{ background: "var(--paid)" }} /> model call · only paid step
            </span>
          </div>

          <div className="panel" style={{ marginTop: 4 }}>
            <div className="panel-head">
              <span>output — validated against schema</span>
              <span className="tag">JSON</span>
            </div>
            <div className="panel-body">
              {phase === "done" ? (
                <pre
                  className="code out-json show"
                  dangerouslySetInnerHTML={{ __html: highlightJSON(ex.output) }}
                />
              ) : (
                <div className="out-empty">
                  <div>
                    <div
                      style={{
                        fontFamily: "var(--mono)",
                        fontSize: 13,
                        color: "var(--void-ink-2)",
                      }}
                    >
                      {running ? "extracting…" : "awaiting run"}
                    </div>
                    <p>
                      Press <strong>Run extraction</strong> to send this document
                      through the pipeline.
                    </p>
                  </div>
                </div>
              )}
            </div>
            {phase === "done" && (
              <div className="result-meta" style={{ display: "flex" }}>
                <span className="chip ok">✓ schema valid</span>
                <span className="chip ok">✓ grounded in source</span>
                <span className="chip">
                  confidence
                  <span className="conf-track">
                    <i style={{ width: `${confWidth}%` }} />
                  </span>
                  <b style={{ color: "var(--valid)" }}>{ex.confidence.toFixed(2)}</b>
                </span>
              </div>
            )}
          </div>

          {phase === "done" && (
            <div className="note-callout" style={{ display: "flex" }}>
              <span className="nc-ic" aria-hidden>◆</span>
              <div>
                <div className="nc-label">{ex.note.label}</div>
                <div className="nc-body">{ex.note.body}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
