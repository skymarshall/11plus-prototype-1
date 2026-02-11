-- =====================================================
-- Remove All Questions and Dependent Data (Supabase)
-- =====================================================
-- Use this before re-running insert_sample_arithmetic_questions_supabase.sql
-- (or any other question insert script) so inserts start from a clean slate.
--
-- Cascades to:
--   answer_options, correct_answers, question_tag_assignments,
--   question_set_items, question_statistics, user_question_attempts,
--   user_question_attempt_option_order
--
-- Then practice_sessions are truncated (they would be empty of attempts anyway).
--
-- Leaves intact: subjects, topics, profiles
-- =====================================================

TRUNCATE questions RESTART IDENTITY CASCADE;
TRUNCATE practice_sessions RESTART IDENTITY CASCADE;

-- Optional: show that questions are gone (run separately if you want to verify)
-- SELECT count(*) AS question_count FROM questions;
