-- =====================================================
-- NVR subject and topic for Supabase (PostgreSQL)
-- Creates subject "Non-Verbal Reasoning" and topic "Shapes".
-- Use the returned/subject and topic IDs with upload_and_insert_questions.py
-- (e.g. run: SELECT id, code FROM subjects WHERE code = 'NVR';
--        SELECT id, name FROM topics WHERE subject_id = (SELECT id FROM subjects WHERE code = 'NVR') AND name = 'Shapes';)
-- =====================================================
-- Run this AFTER create_11plus_supabase.sql
-- Paste into Supabase Dashboard → SQL Editor → Run
-- =====================================================

-- Insert Non-Verbal Reasoning subject (idempotent)
INSERT INTO subjects (name, code, description)
VALUES ('Non-Verbal Reasoning', 'NVR', 'Non-verbal reasoning: shapes, patterns, odd one out, and diagram questions')
ON CONFLICT (code) DO NOTHING;

-- Insert Shapes topic (idempotent). Root-level: parent_topic_id NULL.
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Shapes', 'Shape-based odd one out and diagram reasoning'
FROM subjects WHERE code = 'NVR'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
