# Supabase waitlist setup

The early-access form writes signups to a Supabase `waitlist` table. The code is
already wired (`lib/supabase.ts`, `components/landing/EmailForm.tsx`). You just need
to create the project and add two env vars. ~5 minutes.

## 1. Create a project

1. Go to https://supabase.com → sign in → **New project**.
2. Pick a name + a strong database password (you won't need it for this).
3. Wait for it to provision.

## 2. Create the table + security policy

Open **SQL Editor** → **New query**, paste this, and run it:

```sql
-- The waitlist table
create table public.waitlist (
  id         uuid primary key default gen_random_uuid(),
  email      text not null,
  created_at timestamptz not null default now()
);

-- One row per email (case-insensitive)
create unique index waitlist_email_key on public.waitlist (lower(email));

-- Lock the table down with row-level security
alter table public.waitlist enable row level security;

-- Anyone may ADD their email…
create policy "anon can join waitlist"
  on public.waitlist
  for insert
  to anon
  with check (true);

-- …and NO ONE can read/update/delete via the public API.
-- (There is no SELECT policy, so the anon key cannot list emails.)
```

> ⚠️ **Why the policy matters:** the anon key ships to every visitor's browser. Row-level
> security is what keeps your list private. With the policy above, the public key can only
> *insert* — it cannot read anyone's email. You view signups yourself in the Supabase
> dashboard (Table Editor → `waitlist`) or via the secret `service_role` key, which never
> goes in the frontend.

## 3. Add the keys to the site

In Supabase: **Project Settings → API**. Copy:

- **Project URL** (e.g. `https://abcdxyz.supabase.co`)
- **anon / public** key (the long one labeled `anon` `public`)

Create `web/.env.local` (this file is git-ignored — never commit keys):

```bash
NEXT_PUBLIC_SUPABASE_URL=https://abcdxyz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...your-anon-key...
```

Then rebuild / restart the dev server so the values are picked up:

```bash
npm run dev      # or: npm run build
```

## 4. Verify

Submit the form on the site, then check **Table Editor → `waitlist`** in Supabase — your
row should be there. To get an email when someone signs up, add a Supabase **Database
Webhook** or a scheduled export later; for now the dashboard is your inbox.

## Notes

- Until the env vars are set, the form still works — it just shows the local
  "you're on the list" confirmation without storing anything.
- `NEXT_PUBLIC_*` vars are inlined at **build time** for static export, so set them
  before `npm run build`.
