import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Public (browser-safe) credentials. The anon key is designed to ship to the
// client; row-level security on the `waitlist` table (see SUPABASE_SETUP.md) is
// what actually protects the data — anon can INSERT, but cannot read the list.
//
// Until these env vars are set in web/.env.local, `supabase` is null and the
// email form falls back to a local "you're on the list" confirmation.
const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase: SupabaseClient | null =
  url && anonKey ? createClient(url, anonKey) : null;
