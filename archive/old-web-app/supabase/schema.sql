-- Run this once in the Supabase SQL editor (a new project's "SQL Editor" tab) before running
-- seed.sql. Safe to re-run: every statement is idempotent (IF NOT EXISTS / OR REPLACE).
--
-- Design: schools + prompts are the app's read-only reference catalog; prompt_similarity is the
-- user-curated reuse matrix. All three are publicly readable (the app queries them with the
-- `anon` key, no login) but not publicly writable - editing happens in this dashboard's own
-- table editor, which uses your authenticated session and bypasses RLS entirely.

create table if not exists schools (
  id text primary key,
  name text not null,
  platform text not null default 'Common app',
  test_optional boolean not null default false,
  english_p25 numeric not null,
  english_p50 numeric not null,
  english_p75 numeric not null,
  math_p25 numeric not null,
  math_p50 numeric not null,
  math_p75 numeric not null,
  difficulty numeric not null,
  importance text not null default 'Considered'
    check (importance in ('Very Important', 'Important', 'Considered', 'Not Considered')),
  acceptance_rate numeric,
  us_news_rank integer,
  created_at timestamptz not null default now()
);

create table if not exists prompts (
  id text primary key,
  school_id text not null references schools (id) on delete cascade,
  text text not null,
  word_limit integer,
  sort_order integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists prompts_school_id_idx on prompts (school_id);

create table if not exists prompt_similarity (
  id uuid primary key default gen_random_uuid(),
  prompt_a_id text not null references prompts (id) on delete cascade,
  prompt_b_id text not null references prompts (id) on delete cascade,
  score numeric not null check (score >= 0 and score <= 100),
  created_at timestamptz not null default now(),
  -- Store each pair exactly once regardless of which order they're entered in.
  constraint prompt_similarity_ordered_pair check (prompt_a_id < prompt_b_id),
  constraint prompt_similarity_unique_pair unique (prompt_a_id, prompt_b_id)
);
create index if not exists prompt_similarity_a_idx on prompt_similarity (prompt_a_id);
create index if not exists prompt_similarity_b_idx on prompt_similarity (prompt_b_id);

-- Free-tier waitlist: the opposite access pattern from the three tables above - public can INSERT
-- (anyone can join the list) but there is no select policy at all, so the anon key can never read
-- emails back. You read signups yourself in the table editor, which uses your authenticated
-- session and bypasses RLS entirely, same as editing schools/prompts/prompt_similarity does.
create table if not exists waitlist_emails (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

alter table waitlist_emails enable row level security;
drop policy if exists "public join waitlist" on waitlist_emails;
create policy "public join waitlist" on waitlist_emails for insert with check (true);

-- Row Level Security: public read, no public write on any of the three catalog tables.
alter table schools enable row level security;
alter table prompts enable row level security;
alter table prompt_similarity enable row level security;

drop policy if exists "public read schools" on schools;
create policy "public read schools" on schools for select using (true);

drop policy if exists "public read prompts" on prompts;
create policy "public read prompts" on prompts for select using (true);

drop policy if exists "public read prompt_similarity" on prompt_similarity;
create policy "public read prompt_similarity" on prompt_similarity for select using (true);

-- Note on prompt_similarity_ordered_pair: since prompt_a_id must sort before prompt_b_id,
-- when *entering* a score in the table editor always put the alphabetically-earlier prompt id
-- in prompt_a_id - otherwise the insert fails the check constraint. This is what keeps a pair
-- from accidentally being scored twice in conflicting directions.
