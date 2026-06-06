import Demo from "@/components/landing/Demo";
import CodeTabs from "@/components/landing/CodeTabs";
import EmailForm from "@/components/landing/EmailForm";
import RevealInit from "@/components/landing/RevealInit";
import Roadmap from "@/components/landing/Roadmap";
import { reliability, GITHUB } from "@/lib/landingData";

export default function Home() {
  return (
    <>
      <RevealInit />

      {/* ============ NAV ============ */}
      <header className="nav">
        <div className="nav-in">
          <a className="logo" href="#top" aria-label="docapi home">
            <span className="mark" aria-hidden="true" />
            docapi<span className="dim">.dev</span>
          </a>
          <nav className="nav-links" aria-label="Primary">
            <a href="#demo">Demo</a>
            <a href="#reliability">Reliability</a>
            <a href="#how">How it works</a>
            <a href={GITHUB}>GitHub</a>
          </nav>
          <div className="nav-right">
            <a className="btn" href={GITHUB}>GitHub</a>
            <a className="btn btn-primary" href="#access">
              Get access
            </a>
          </div>
        </div>
      </header>

      <main id="top">
        {/* ============ HERO ============ */}
        <section className="hero">
          <div className="wrap hero-grid">
            <div>
              <span className="eyebrow">Open-source document extraction API</span>
              <h1>
                Reliable document extraction for <span className="u">AI&nbsp;agents</span>.
              </h1>
              <p className="sub">
                Give it a file and the fields you want. Get back JSON guaranteed to match
                your schema — or a precise, structured error.{" "}
                <strong>Never silently-wrong data.</strong>
              </p>
              <div className="badges" aria-label="Project facts">
                <span className="badge"><b>✓</b> Apache-2.0</span>
                <span className="badge"><b>✓</b> Runs 100% local — $0</span>
                <span className="badge"><b>✓</b> REST + MCP</span>
                <span className="badge"><b>✓</b> 80 tests passing</span>
              </div>
              <div className="hero-cta">
                <a className="btn btn-primary btn-lg" href="#demo">See it work →</a>
                <a className="btn btn-lg" href={GITHUB}>★ Star on GitHub</a>
              </div>
            </div>

            <aside className="proof-card" aria-label="Example extraction">
              <div className="pc-bar">
                <span className="pc-dot" /><span className="pc-dot" /><span className="pc-dot" />
                <span style={{ marginLeft: 6 }}>razorpay_receipt.pdf → schema</span>
              </div>
              <div className="pc-flow">
                <div className="pc-row">
                  <span className="ic" aria-hidden="true">›</span>
                  <span className="k">source</span>
                  <span className="v">Payment Date: 26-05-2025</span>
                </div>
                <div className="pc-row">
                  <span className="ic err" aria-hidden="true">✕</span>
                  <span className="k">model alone</span>
                  <span className="v bad">&quot;year&quot;: 2605</span>
                </div>
                <div className="pc-row">
                  <span className="ic" aria-hidden="true">✓</span>
                  <span className="k">docapi</span>
                  <span className="v good">&quot;2025-05-26&quot;</span>
                </div>
                <div className="pc-row">
                  <span className="ic" aria-hidden="true">✓</span>
                  <span className="k">grounded</span>
                  <span className="v good">confidence 0.98</span>
                </div>
              </div>
            </aside>
          </div>
        </section>

        {/* ============ DEMO ============ */}
        <section className="section demo-wrap" id="demo">
          <span className="section-index">§ 01 / DEMO</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">Live, in your browser</span>
              <h2>Watch a messy document become schema-valid JSON.</h2>
              <p>
                Three real documents, three schemas. Hit <em>Run extraction</em> and watch
                the six-stage pipeline — only one stage ever touches a model. Everything
                here runs client-side.
              </p>
            </div>
            <div className="reveal">
              <Demo />
            </div>
          </div>
        </section>

        {/* ============ PROBLEM ============ */}
        <section className="section problem" id="problem">
          <span className="section-index">§ 02 / PROBLEM</span>
          <div className="wrap problem-grid">
            <div className="reveal">
              <span className="eyebrow">The problem</span>
              <h2>Agents are impressive — until a real PDF hits them.</h2>
              <p className="lead">
                Hand a model a scanned receipt or a two-column invoice and it will
                confidently return something. The question is whether you can trust it.
              </p>
              <p className="body">
                docapi validates every response against <b>your</b> schema, verifies the
                values are actually present in the source text, and repairs what code can
                repair. When it can&apos;t comply, it returns a <b>structured error</b> —
                not a plausible guess your agent will act on.
              </p>
            </div>
            <div className="fail-list reveal" aria-label="Common failure modes">
              <div className="fail-row">
                <span className="fic" aria-hidden="true">✕</span>
                <div>
                  <div className="ft">Hallucinated values</div>
                  <div className="fd">A total or date that reads well but was never in the document.</div>
                </div>
              </div>
              <div className="fail-row">
                <span className="fic" aria-hidden="true">✕</span>
                <div>
                  <div className="ft">Half-broken shapes</div>
                  <div className="fd">Missing fields, wrong types, an array where you needed an object.</div>
                </div>
              </div>
              <div className="fail-row">
                <span className="fic" aria-hidden="true">✕</span>
                <div>
                  <div className="ft">Silent failure</div>
                  <div className="fd">No error, no flag — just wrong data flowing straight into your pipeline.</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ============ RELIABILITY ============ */}
        <section className="section" id="reliability">
          <span className="section-index">§ 03 / RELIABILITY</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">The reliability engine</span>
              <h2>Six guarantees between the model and your data.</h2>
              <p>Every extraction passes through the same checks. None of them are the model grading its own work.</p>
            </div>
            <div className="rel-grid reveal">
              {reliability.map((r) => (
                <div className="rel-card" key={r.n}>
                  <div className="rn">{r.n}</div>
                  <h3>{r.title}</h3>
                  <p>{r.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ============ AGENT-NATIVE CODE ============ */}
        <section className="section code-wrap" id="code">
          <span className="section-index">§ 04 / INTEGRATE</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">Agent-native</span>
              <h2>One core. Three ways to call it.</h2>
              <p>A REST endpoint, an MCP tool your agent invokes directly, or a Python call. Same engine, same guarantees behind all three.</p>
            </div>
            <div className="reveal">
              <CodeTabs />
            </div>
          </div>
        </section>

        {/* ============ HOW IT WORKS ============ */}
        <section className="section" id="how">
          <span className="section-index">§ 05 / PIPELINE</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">How it works</span>
              <h2>The six-stage pipeline, in order.</h2>
              <p>
                Only the <em>understand</em> step can ever cost money or call a network.
                Everything else is deterministic, local, and free.
              </p>
            </div>
            <div className="steps reveal">
              <Step n="01" title="Ingest" desc="Accept the file. Detect type, page count, and encoding before anything else runs." cost="free" costLabel="free · local" />
              <Step n="02" title="Extract text" desc="Pull raw text and layout from the document, with an OCR fallback for scans and images." cost="free" costLabel="free · local" />
              <Step n="03" title="Understand" desc="The single model call: map the messy text onto your requested fields. Runs locally via Ollama for $0, or via Claude when you want it." cost="paid" costLabel="model call" />
              <Step n="04" title="Validate (+ retry)" desc="Check the result against your schema. If it fails, feed the exact error back and retry once — then error out cleanly if needed." cost="free" costLabel="free · local" />
              <Step n="05" title="Normalize" desc="Repair dates, numbers, and currency in code. Deterministic, testable, identical every run." cost="free" costLabel="free · local" />
              <Step n="06" title="Ground + score" desc="Verify every extracted value is present in the source text, flag anything that isn't, and emit a confidence signal." cost="free" costLabel="free · local" />
            </div>
            <div className="howit-note">
              <span className="sw" style={{ background: "var(--paid)" }} />
              Five of six stages never leave your machine — the model call is the only billable, networked step.
            </div>
          </div>
        </section>

        {/* ============ ROADMAP (orbital) ============ */}
        <section className="section" id="roadmap" style={{ paddingBottom: 40 }}>
          <span className="section-index">§ 06 / ROADMAP</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">Roadmap</span>
              <h2>What&apos;s shipped, and what&apos;s next.</h2>
              <p>
                The reliability engine is here today. Tap any node in the orbit to expand
                it and trace its connected milestones.
              </p>
              <div className="orbital-hint">
                <span className="sw" /> Click a node to explore · auto-orbiting
              </div>
            </div>
          </div>
          {/* full-bleed dark orbital */}
          <Roadmap />
        </section>

        {/* ============ OPEN-CORE / PRICING ============ */}
        <section className="section" id="access">
          <span className="section-index">§ 07 / GET ACCESS</span>
          <div className="wrap">
            <div className="section-head reveal">
              <span className="eyebrow">Open-core</span>
              <h2>Free and local today. Hosted when you need scale.</h2>
              <p>
                The open-source core is the whole engine — not a crippled demo. A hosted
                version is coming for teams that would rather not run a model themselves.
              </p>
            </div>
            <div className="price-grid reveal">
              <div className="price-card now">
                <span className="price-tag avail">● Available now</span>
                <h3>Open source</h3>
                <p className="pdesc">The full reliability engine, Apache-2.0. Clone it, run it, ship it.</p>
                <ul className="price-feats">
                  <li><span className="fk">✓</span> Apache-2.0 — yours to fork and self-host</li>
                  <li><span className="fk">✓</span> Runs 100% local via Ollama — $0 per extraction</li>
                  <li><span className="fk">✓</span> REST API <em>and</em> MCP tool out of the box</li>
                  <li><span className="fk">✓</span> Schema validation, grounding, date repair, retries</li>
                </ul>
                <div className="spacer" />
                <a className="btn btn-primary btn-lg" href={GITHUB}>★ Get it on GitHub</a>
              </div>

              <div className="price-card">
                <span className="price-tag soon">○ Coming soon</span>
                <h3>Hosted docapi</h3>
                <p className="pdesc">An API key instead of a local model. Auth, metering, and scale — built for production agents.</p>
                <ul className="price-feats soon">
                  <li><span className="fk">→</span> API key instead of running your own model</li>
                  <li><span className="fk">→</span> Auth, usage metering, and rate limits</li>
                  <li><span className="fk">→</span> Seconds, not minutes, on long documents</li>
                  <li><span className="fk">→</span> Same engine, same guarantees, zero ops</li>
                </ul>
                <div className="spacer" />
                <EmailForm />
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ============ FOOTER ============ */}
      <footer className="footer">
        <div className="wrap footer-in">
          <div className="fcol">
            <a className="logo" href="#top" aria-label="docapi home">
              <span className="mark" aria-hidden="true" />docapi<span className="dim">.dev</span>
            </a>
            <span className="building">Building in public</span>
          </div>
          <div className="fcol">
            <span className="fhead">Product</span>
            <a href="#demo">Demo</a>
            <a href="#reliability">Reliability</a>
            <a href="#how">How it works</a>
          </div>
          <div className="fcol">
            <span className="fhead">Source</span>
            <a href={GITHUB}>GitHub</a>
            <a href={GITHUB}>REST + MCP</a>
            <span>Apache-2.0</span>
          </div>
          <div className="fcol">
            <span className="fhead">Get access</span>
            <a href="#access">Hosted early access</a>
            <a href="#access">Run it locally</a>
          </div>
        </div>
      </footer>
    </>
  );
}

function Step({
  n,
  title,
  desc,
  cost,
  costLabel,
}: {
  n: string;
  title: string;
  desc: string;
  cost: "free" | "paid";
  costLabel: string;
}) {
  return (
    <div className="step">
      <div className="sn">{n}</div>
      <div>
        <div className="st">{title}</div>
        <div className="sd">{desc}</div>
      </div>
      <div className={`scost ${cost}`}>{costLabel}</div>
    </div>
  );
}
