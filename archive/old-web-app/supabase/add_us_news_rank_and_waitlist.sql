-- Run this once in your existing project's SQL editor to catch it up to the latest schema.sql.
-- Safe to re-run: every statement is idempotent.
--
-- 1. Adds a nullable us_news_rank column to schools, and fills in the 5 schools that already have
--    complete data (see supabase/update_five_schools.sql) with their real 2026 US News National
--    Universities rank. Every other school is left null - fill those in via the table editor
--    whenever you have them, same as acceptance_rate today.
-- 2. Creates the waitlist_emails table for the "5 schools free, email us for premium" flow -
--    public can INSERT (join the list) but there's no select policy, so the app can never read
--    emails back; you read signups yourself in the table editor (authenticated, bypasses RLS).

alter table schools add column if not exists us_news_rank integer;

-- 2026 US News National Universities rank (usnews.com/best-colleges/rankings/national-universities,
-- verified via collegekickstart.com's summary of the same rankings). Purdue is tied at 46.
update schools set us_news_rank = 1 where id = 'princeton';
update schools set us_news_rank = 2 where id = 'mit';
update schools set us_news_rank = 4 where id = 'stanford';
update schools set us_news_rank = 32 where id = 'georgia-tech';
update schools set us_news_rank = 46 where id = 'purdue';

create table if not exists waitlist_emails (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

alter table waitlist_emails enable row level security;
drop policy if exists "public join waitlist" on waitlist_emails;
create policy "public join waitlist" on waitlist_emails for insert with check (true);
