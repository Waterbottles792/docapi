"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";

type Status = "idle" | "sending" | "done" | "error";

export default function EmailForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [invalid, setInvalid] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setStatus("sending");

    if (supabase) {
      const { error } = await supabase
        .from("waitlist")
        .insert({ email: email.trim().toLowerCase() });
      // 23505 = unique violation → already signed up; treat as success.
      if (error && error.code !== "23505") {
        setStatus("error");
        return;
      }
    }
    // No Supabase configured yet → still confirm locally so the UX never breaks.
    setStatus("done");
  };

  if (status === "done") {
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
            if (status === "error") setStatus("idle");
          }}
          style={invalid ? { borderColor: "var(--error)" } : undefined}
        />
        <button className="btn btn-primary" type="submit" disabled={status === "sending"}>
          {status === "sending" ? "…" : "Request access"}
        </button>
      </form>
      {status === "error" ? (
        <p className="email-note" style={{ color: "var(--error)" }}>
          Something went wrong — please try again.
        </p>
      ) : (
        <p className="email-note">Early-access list. No spam, one launch email.</p>
      )}
    </>
  );
}
