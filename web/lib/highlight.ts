// Pure string highlighters ported from the original app.js — no DOM access,
// safe to call from client components and feed via dangerouslySetInnerHTML
// (all inputs are our own canned data).

export const esc = (s: unknown): string =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function highlightJSON(value: unknown): string {
  const json = JSON.stringify(value, null, 2);
  return json
    .replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
      (m) => {
        let cls = "j-num";
        if (/^"/.test(m)) {
          cls = /:$/.test(m) ? "j-key" : "j-str";
        } else if (/true|false|null/.test(m)) {
          cls = "j-num";
        }
        return '<span class="' + cls + '">' + esc(m) + "</span>";
      },
    )
    .replace(/[{}[\],]/g, (m) => '<span class="j-punc">' + m + "</span>");
}

/* schema rendered as a compact pseudo-type block */
export function renderSchema(schema: unknown): string {
  const json = JSON.stringify(schema, null, 2);
  return esc(json)
    .replace(/"(\w+)":/g, '<span class="j-key">"$1":</span>')
    .replace(/: (".*?")/g, ': <span class="j-str">$1</span>');
}

/* highlight a date token inside source text */
export function renderSource(text: string): string {
  let html = esc(text);
  html = html.replace(
    /(\d{2}-\d{2}-\d{4}|\d{2}\/\d{2}\/\d{4})/g,
    '<span class="hl-date">$1</span>',
  );
  return html;
}

/* lightweight token highlighter per language */
export function highlightCode(code: string, lang: string): string {
  let h = esc(code);
  if (lang === "bash") {
    h = h
      .replace(/(#.*)$/gm, '<span class="cm-cmt">$1</span>')
      .replace(
        /(&#39;[^&]*?&#39;|&quot;[^&]*?&quot;|'[^']*?'|"[^"]*?")/g,
        '<span class="cm-str">$1</span>',
      );
  } else if (lang === "json") {
    h = h
      .replace(/(\/\/.*)$/gm, '<span class="cm-cmt">$1</span>')
      .replace(/("[\w.\-]+")(\s*:)/g, '<span class="cm-key">$1</span>$2')
      .replace(/:\s*("[^"]*?")/g, ': <span class="cm-str">$1</span>');
  } else if (lang === "python") {
    h = h
      .replace(/(#.*)$/gm, '<span class="cm-cmt">$1</span>')
      .replace(
        /\b(from|import|def|return|str|float|int)\b/g,
        '<span class="cm-kw">$1</span>',
      )
      .replace(
        /(&quot;[^&]*?&quot;|&#39;[^&]*?&#39;|'[^']*?'|"[^"]*?")/g,
        '<span class="cm-str">$1</span>',
      )
      .replace(/\b(\d+\.?\d*)\b/g, '<span class="cm-num">$1</span>');
  }
  return h;
}
