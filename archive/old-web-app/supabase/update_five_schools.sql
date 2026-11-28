-- Makes MIT, Princeton, Stanford, Georgia Tech, and Purdue fully accurate and complete for the
-- 2026-27 application cycle, researched from each school's own admissions pages, recent Common
-- Data Sets, and reporting on this cycle's changes (see the summary the assistant gave you for
-- sources). This is the reference example for what "complete" data looks like when you add more
-- schools yourself: real percentile bands, real acceptance rate, a considered `importance`
-- rating, and every current prompt with its real word limit.
--
-- Safe to run once against your existing project (run supabase/schema.sql and supabase/seed.sql
-- first if you haven't already). Re-running this file is safe too - it deletes and reinserts only
-- these 5 schools' prompts, and prompt_similarity rows referencing them cascade-delete
-- automatically (see the `on delete cascade` in schema.sql), then get reinserted below.

-- ============================================================================
-- 1. School-level fields
-- ============================================================================

-- MIT: test required, own application portal (not Common App). Essay-heavy: 4 main essays
-- (100-200 words) + 4 short responses (40-50 words) + an optional additional-info box.
-- CDS 2025-26 does not rate standardized testing "Very Important" (that's reserved for
-- "personal characteristics"), so "Important" fits better than "Very Important".
update schools set
  name = 'MIT',
  platform = 'Custom',
  test_optional = false,
  english_p25 = 740, english_p50 = 760, english_p75 = 780,
  math_p25 = 780, math_p50 = 800, math_p75 = 800,
  difficulty = 90,
  importance = 'Important',
  acceptance_rate = 0.0456
where id = 'mit';

-- Princeton: still test-optional for THIS cycle (2026-27); mandatory starting 2027-28. CDS rates
-- testing "Very Important" even while optional. Also requires a graded academic paper - modeled
-- as a prompt with no word limit, same as the rest.
update schools set
  name = 'Princeton',
  platform = 'Common app',
  test_optional = true,
  english_p25 = 720, english_p50 = 745, english_p75 = 770,
  math_p25 = 740, math_p50 = 775, math_p75 = 800,
  difficulty = 95,
  importance = 'Very Important',
  acceptance_rate = 0.039
where id = 'princeton';

-- Stanford: reinstated a testing requirement for Fall 2026 entry onward (no longer optional), and
-- its 2025-26 CDS moved testing back to "Very Important". 8 total prompts (5 short-answer @ 50
-- words, 3 essays @ 250 words) is a real, substantial workload - raised difficulty accordingly.
update schools set
  name = 'Stanford',
  platform = 'Common app',
  test_optional = false,
  english_p25 = 720, english_p50 = 745, english_p75 = 770,
  math_p25 = 750, math_p50 = 775, math_p75 = 800,
  difficulty = 75,
  importance = 'Very Important',
  acceptance_rate = 0.038
where id = 'stanford';

-- Georgia Tech: announced July 29, 2026 (days before the 2026-27 cycle opened) that it is
-- eliminating its supplemental essay entirely - applicants now submit only the shared Common App
-- personal essay, which this tool doesn't track per-school. Difficulty dropped accordingly since
-- there's effectively no school-specific writing left. Now requires SAT/ACT (dropped test-optional).
update schools set
  name = 'Georgia Tech',
  platform = 'Common app',
  test_optional = false,
  english_p25 = 670, english_p50 = 715, english_p75 = 760,
  math_p25 = 700, math_p50 = 745, math_p75 = 790,
  difficulty = 5,
  importance = 'Very Important',
  acceptance_rate = 0.127
where id = 'georgia-tech';

-- Purdue: percentile bands already matched its current Common Data Set exactly, and its 2 prompts
-- (250 words each) were already accurate - only the acceptance rate was missing.
update schools set
  acceptance_rate = 0.434
where id = 'purdue';

-- Bonus: fix inconsistent capitalization left over from the original spreadsheet import.
update schools set name = 'Brown' where id = 'brown';
update schools set name = 'Cornell' where id = 'cornell';
update schools set name = 'Northeastern' where id = 'northeastern';
update schools set name = 'Northwestern' where id = 'north-western';
update schools set name = 'University of Pennsylvania' where id = 'upenn';
update schools set name = 'Johns Hopkins University' where id = 'john';

-- ============================================================================
-- 2. Prompts: replace with the complete, current (2026-27) set for MIT/Princeton/Stanford,
--    and clear Georgia Tech's (it no longer has one). Purdue's existing 2 prompts are untouched.
-- ============================================================================

delete from prompts where school_id in ('mit', 'princeton', 'stanford', 'georgia-tech');

insert into prompts (id, school_id, text, word_limit, sort_order) values
  ('mit--field-of-study', 'mit', 'What field of study appeals to you the most right now? Reflect on what has led to this interest.', 200, 0),
  ('mit--unconventional-path', 'mit', 'While some reach their goals following well-trodden paths, others blaze their own trails achieving the unexpected. In what ways have you done something different than what was expected in your educational journey?', 200, 1),
  ('mit--personal-academic-experiences', 'mit', 'How have your personal and academic experiences influenced the types of problems you would want to tackle with an MIT education and the impact you aim to make on your community?', 200, 2),
  ('mit--unexpected-challenge', 'mit', 'How did you manage a situation or challenge that you didn''t expect? What did you learn from it?', 200, 3),
  ('mit--just-for-fun', 'mit', 'What do you do just for fun?', 50, 4),
  ('mit--someone-you-admire', 'mit', 'Who is someone you admire, whether you know them personally or look up to them from afar? Tell us why.', 50, 5),
  ('mit--topic-you-could-talk-about', 'mit', 'What''s a topic, academic or non-academic, that you could talk about for hours?', 50, 6),
  ('mit--generalist-or-specialist', 'mit', 'MIT values both "generalists" with varied interests and "specialists" who focus deeply on one or a few passions. Which do you think best describes you, and why?', 50, 7),
  ('mit--additional-information', 'mit', 'Additional information you would like the admissions committee to know (optional).', null, 8);

insert into prompts (id, school_id, text, word_limit, sort_order) values
  ('princeton--lived-experience', 'princeton', 'As a prospective member of Princeton''s community, reflect on how your lived experiences will impact the conversations you will have in the classroom, the dining hall or other campus spaces. What lessons have you learned in life thus far? What will your classmates learn from you? In short, how has your lived experience shaped you?', 500, 0),
  ('princeton--civic-engagement', 'princeton', 'Princeton has a longstanding commitment to understanding our responsibility to society through service and civic engagement. How does your own story intersect with these ideals?', 250, 1),
  ('princeton--academic-interest', 'princeton', 'What academic areas most pique your curiosity, and how do the programs offered at Princeton suit your particular interests?', 250, 2),
  ('princeton--new-skill', 'princeton', 'What is a new skill you would like to learn in college?', 50, 3),
  ('princeton--brings-joy', 'princeton', 'What brings you joy?', 50, 4),
  ('princeton--soundtrack-song', 'princeton', 'What song represents the soundtrack of your life at this moment?', 50, 5),
  ('princeton--submit-a-paper', 'princeton', 'Submit a graded written paper from your junior or senior year that reflects your writing skills.', null, 6);

insert into prompts (id, school_id, text, word_limit, sort_order) values
  ('stanford--significant-challenge', 'stanford', 'What is the most significant challenge that society faces today?', 50, 0),
  ('stanford--last-two-summers', 'stanford', 'How did you spend your last two summers?', 50, 1),
  ('stanford--historical-moment', 'stanford', 'What historical moment or event do you wish you could have witnessed?', 50, 2),
  ('stanford--extracurricular-elaborate', 'stanford', 'Briefly elaborate on one of your extracurricular activities, a job you hold, or responsibilities you have for your family.', 50, 3),
  ('stanford--five-things-important', 'stanford', 'List five things that are important to you.', 50, 4),
  ('stanford--excited-about-learning', 'stanford', 'The Stanford community is deeply curious and driven to learn in and out of the classroom. Reflect on an idea or experience that makes you genuinely excited about learning.', 250, 5),
  ('stanford--roommate-note', 'stanford', 'Virtually all of Stanford''s undergraduates live on campus. Write a note to your future roommate that reveals something about you or that will help your roommate - and us - get to know you better.', 250, 6),
  ('stanford--distinctive-contribution', 'stanford', 'Please describe what aspects of your life experiences, interests and character would help you make a distinctive contribution as an undergraduate to Stanford University.', 250, 7);

-- Georgia Tech: no insert - it has zero supplemental prompts for 2026-27.

-- ============================================================================
-- 3. A handful of real cross-school prompt-similarity scores, so the reuse feature has something
--    to show immediately (e.g. mark MIT "Applying" and check Princeton/Stanford's estimated
--    reuse on the Difficulty page). Add more over time via the table editor.
-- ============================================================================

insert into prompt_similarity (prompt_a_id, prompt_b_id, score) values
  ('mit--field-of-study', 'princeton--academic-interest', 80),
  ('mit--personal-academic-experiences', 'princeton--civic-engagement', 60),
  ('mit--unconventional-path', 'princeton--lived-experience', 55),
  ('mit--field-of-study', 'stanford--excited-about-learning', 75),
  ('princeton--lived-experience', 'stanford--distinctive-contribution', 80),
  ('princeton--civic-engagement', 'stanford--significant-challenge', 55),
  ('mit--just-for-fun', 'stanford--five-things-important', 40),
  ('mit--field-of-study', 'purdue--briefly-discuss-your-reasons-for-choosing', 45),
  ('princeton--academic-interest', 'purdue--briefly-discuss-your-reasons-for-choosing', 50),
  ('purdue--how-will-opportunities-at-purdue-support', 'stanford--excited-about-learning', 40)
on conflict (prompt_a_id, prompt_b_id) do update set score = excluded.score;
