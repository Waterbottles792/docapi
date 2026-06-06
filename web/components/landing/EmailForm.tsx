"use client";

import { useState } from "react";

export default function EmailForm() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [invalid, setInvalid] = useState(false);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    // No backend yet — wire SITE endpoint (e.g. Formspree) here later.
    setDone(true);
  };

  if (done) {
    return (
      <div className="email-ok show">
        <span aria-hidden>✓</span> You&apos;re on the list — we&apos;ll email you
        when hosted docapi opens up.
      </div>
    );
  }

  return (
    <>
      <form className="email-form" onSubmit={submit} noValidate>
        <input
          type="email"
          placeholder="you@company.com"
          aria-label="Email for early access"
          autoComplete="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setInvalid(false);
          }}
          style={invalid ? { borderColor: "var(--error)" } : undefined}
        />
        <button className="btn btn-primary" type="submit">
          Request access
        </button>
      </form>
      <p className="email-note">Early-access list. No spam, one launch email.</p>
    </>
  );
}
