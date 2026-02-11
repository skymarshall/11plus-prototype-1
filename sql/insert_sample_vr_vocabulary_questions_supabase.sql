-- =====================================================
-- Sample VR Vocabulary Questions for Supabase (PostgreSQL)
-- 50 Multiple Choice Questions: Synonyms & Antonyms
-- =====================================================
-- Run this AFTER create_11plus_supabase.sql
-- Paste into Supabase Dashboard → SQL Editor → Run
-- =====================================================

-- Insert Verbal Reasoning subject (idempotent)
INSERT INTO subjects (name, code, description)
VALUES ('Verbal Reasoning', 'VR', 'Vocabulary, synonyms, antonyms, and verbal logic')
ON CONFLICT (code) DO NOTHING;

-- Insert topics: Synonyms, Antonyms (root-level: parent_topic_id NULL)
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Synonyms', 'Words with the same or similar meaning' FROM subjects WHERE code = 'VR'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;

INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Antonyms', 'Words with opposite meanings' FROM subjects WHERE code = 'VR'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;

DO $$
DECLARE
  sid INT;
  t_syn INT;
  t_ant INT;
  qid INT;
BEGIN
  SELECT id INTO sid FROM subjects WHERE code = 'VR';
  SELECT id INTO t_syn FROM topics WHERE subject_id = sid AND name = 'Synonyms' AND parent_topic_id IS NULL;
  SELECT id INTO t_ant FROM topics WHERE subject_id = sid AND name = 'Antonyms' AND parent_topic_id IS NULL;

  -- ========== SYNONYMS (Q1–Q25) ==========

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to HAPPY?', 'Joyful means the same as happy; both describe a positive, cheerful feeling.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Sad',false,1),(qid,'Joyful',true,2),(qid,'Angry',false,3),(qid,'Tired',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to BIG?', 'Enormous means very big; it is a synonym that emphasises size.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Tiny',false,1),(qid,'Enormous',true,2),(qid,'Short',false,3),(qid,'Narrow',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to BRAVE?', 'Courageous means brave; both describe someone who faces danger without fear.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Scared',false,1),(qid,'Courageous',true,2),(qid,'Quiet',false,3),(qid,'Lazy',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to ANCIENT?', 'Antique means old and from the past, similar to ancient.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Modern',false,1),(qid,'New',false,2),(qid,'Antique',true,3),(qid,'Fresh',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to WEARY?', 'Weary means tired or exhausted; fatigued has the same meaning.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Energetic',false,1),(qid,'Fatigued',true,2),(qid,'Excited',false,3),(qid,'Cheerful',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to BRILLIANT?', 'Brilliant can mean very clever or intelligent; ingenious is a synonym for clever and inventive.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Dull',false,1),(qid,'Ingenious',true,2),(qid,'Stupid',false,3),(qid,'Simple',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to RELUCTANT?', 'Reluctant means unwilling; hesitant means hesitating or unwilling to act.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Eager',false,1),(qid,'Hesitant',true,2),(qid,'Keen',false,3),(qid,'Enthusiastic',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to MYSTERIOUS?', 'Mysterious means puzzling and hard to understand; enigmatic means the same.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Clear',false,1),(qid,'Obvious',false,2),(qid,'Enigmatic',true,3),(qid,'Plain',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to ABUNDANT?', 'Abundant means plentiful or in large supply; copious means the same.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Scarce',false,1),(qid,'Copious',true,2),(qid,'Rare',false,3),(qid,'Sparse',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to FEEBLE?', 'Feeble means weak; frail means weak and delicate.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Strong',false,1),(qid,'Frail',true,2),(qid,'Powerful',false,3),(qid,'Robust',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to CONCEAL?', 'Conceal means to hide; disguise means to hide the real appearance or nature of something.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Reveal',false,1),(qid,'Disguise',true,2),(qid,'Expose',false,3),(qid,'Show',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to RAPID?', 'Rapid means fast; swift means moving or happening quickly.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Slow',false,1),(qid,'Swift',true,2),(qid,'Sluggish',false,3),(qid,'Delayed',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to FRIENDLY?', 'Amiable means friendly and likeable.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Hostile',false,1),(qid,'Amiable',true,2),(qid,'Cold',false,3),(qid,'Rude',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to PERSEVERE?', 'Persevere means to continue despite difficulty; persist means the same.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Quit',false,1),(qid,'Persist',true,2),(qid,'Surrender',false,3),(qid,'Abandon',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to EBULLIENT?', 'Ebullient means cheerful and full of energy; exuberant means the same.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Gloomy',false,1),(qid,'Exuberant',true,2),(qid,'Melancholy',false,3),(qid,'Listless',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to LACONIC?', 'Laconic means using very few words; concise means brief and to the point.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Verbose',false,1),(qid,'Concise',true,2),(qid,'Lengthy',false,3),(qid,'Wordy',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to PRUDENT?', 'Prudent means wise and careful; cautious means careful to avoid risk.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Reckless',false,1),(qid,'Cautious',true,2),(qid,'Rash',false,3),(qid,'Careless',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to GENEROUS?', 'Generous means giving freely; benevolent means kind and generous.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Stingy',false,1),(qid,'Benevolent',true,2),(qid,'Selfish',false,3),(qid,'Mean',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to VIGOROUS?', 'Vigorous means strong and full of energy; robust means strong and healthy.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Weak',false,1),(qid,'Robust',true,2),(qid,'Feeble',false,3),(qid,'Lethargic',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to CALM?', 'Serene means calm and peaceful.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Agitated',false,1),(qid,'Serene',true,2),(qid,'Anxious',false,3),(qid,'Nervous',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to SMALL?', 'Minute (pronounced my-NOOT) can mean very small; here we use it as an adjective meaning tiny.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Huge',false,1),(qid,'Minute',true,2),(qid,'Giant',false,3),(qid,'Massive',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to ASTUTE?', 'Astute means shrewd and clever; perceptive means having insight and understanding.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Dense',false,1),(qid,'Perceptive',true,2),(qid,'Obtuse',false,3),(qid,'Slow',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to OBFUSCATE?', 'Obfuscate means to make unclear or confusing; obscure means to hide or make difficult to understand.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Clarify',false,1),(qid,'Obscure',true,2),(qid,'Illuminate',false,3),(qid,'Explain',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to BEGIN?', 'Commence means to begin or start.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Finish',false,1),(qid,'Commence',true,2),(qid,'End',false,3),(qid,'Conclude',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to MALICIOUS?', 'Malicious means intending to do harm; spiteful means the same.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Kind',false,1),(qid,'Spiteful',true,2),(qid,'Benevolent',false,3),(qid,'Gentle',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to FLAW?', 'A flaw is a defect or imperfection; blemish means a small mark or flaw.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Strength',false,1),(qid,'Blemish',true,2),(qid,'Virtue',false,3),(qid,'Perfection',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to EPHEMERAL?', 'Ephemeral means lasting for a very short time; transient means the same.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Permanent',false,1),(qid,'Transient',true,2),(qid,'Eternal',false,3),(qid,'Lasting',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to LOUD?', 'Noisy means making a lot of noise, similar to loud.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Quiet',false,1),(qid,'Noisy',true,2),(qid,'Silent',false,3),(qid,'Peaceful',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_syn, 'multiple_choice', 'Which word is closest in meaning to WRETCHED?', 'Wretched means very unhappy or of poor quality; miserable means very unhappy.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Joyful',false,1),(qid,'Miserable',true,2),(qid,'Delighted',false,3),(qid,'Content',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- ========== ANTONYMS (Q26–Q50) ==========

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to HOT?', 'Cold is the opposite of hot.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Cold',true,1),(qid,'Warm',false,2),(qid,'Boiling',false,3),(qid,'Sunny',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to DARK?', 'Light is the opposite of dark.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Black',false,1),(qid,'Light',true,2),(qid,'Shadow',false,3),(qid,'Gloomy',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to ANCIENT?', 'Modern means of the present time; the opposite of ancient.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Old',false,1),(qid,'Modern',true,2),(qid,'Antique',false,3),(qid,'Historic',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to BRAVE?', 'Cowardly means lacking courage; the opposite of brave.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Bold',false,1),(qid,'Cowardly',true,2),(qid,'Fearless',false,3),(qid,'Heroic',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to GENEROUS?', 'Stingy means unwilling to give; the opposite of generous.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Kind',false,1),(qid,'Stingy',true,2),(qid,'Charitable',false,3),(qid,'Giving',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to RELUCTANT?', 'Reluctant means unwilling; eager means very willing.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Hesitant',false,1),(qid,'Eager',true,2),(qid,'Unwilling',false,3),(qid,'Resistant',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to ABUNDANT?', 'Abundant means plentiful; scarce means in short supply.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Plentiful',false,1),(qid,'Scarce',true,2),(qid,'Copious',false,3),(qid,'Bountiful',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to FEEBLE?', 'Feeble means weak; robust means strong and healthy.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Frail',false,1),(qid,'Robust',true,2),(qid,'Weak',false,3),(qid,'Delicate',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to RAPID?', 'Rapid means fast; sluggish means slow.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Swift',false,1),(qid,'Sluggish',true,2),(qid,'Quick',false,3),(qid,'Speedy',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to FRIENDLY?', 'Hostile means unfriendly or aggressive.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Amiable',false,1),(qid,'Hostile',true,2),(qid,'Warm',false,3),(qid,'Kind',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to PERSEVERE?', 'Persevere means to continue; abandon means to give up.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Persist',false,1),(qid,'Abandon',true,2),(qid,'Continue',false,3),(qid,'Endure',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to EBULLIENT?', 'Ebullient means cheerful and energetic; listless means lacking energy.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Exuberant',false,1),(qid,'Listless',true,2),(qid,'Vivacious',false,3),(qid,'Animated',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to LACONIC?', 'Laconic means using few words; verbose means using too many words.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Concise',false,1),(qid,'Verbose',true,2),(qid,'Brief',false,3),(qid,'Terse',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to PRUDENT?', 'Prudent means careful; reckless means careless and rash.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Cautious',false,1),(qid,'Reckless',true,2),(qid,'Careful',false,3),(qid,'Sensible',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to CALM?', 'Agitated means nervous and unable to relax; the opposite of calm.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Serene',false,1),(qid,'Agitated',true,2),(qid,'Peaceful',false,3),(qid,'Placid',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to VIGOROUS?', 'Vigorous means strong and energetic; lethargic means sluggish and lacking energy.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Robust',false,1),(qid,'Lethargic',true,2),(qid,'Energetic',false,3),(qid,'Dynamic',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to BEGIN?', 'Conclude means to bring to an end; the opposite of begin.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Start',false,1),(qid,'Conclude',true,2),(qid,'Commence',false,3),(qid,'Initiate',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to MALICIOUS?', 'Malicious means intending harm; benevolent means kind and well-meaning.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Spiteful',false,1),(qid,'Benevolent',true,2),(qid,'Vindictive',false,3),(qid,'Cruel',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to EPHEMERAL?', 'Ephemeral means short-lived; permanent means lasting forever.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Transient',false,1),(qid,'Permanent',true,2),(qid,'Brief',false,3),(qid,'Fleeting',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to LOUD?', 'Silent means making no sound; the opposite of loud.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Noisy',false,1),(qid,'Silent',true,2),(qid,'Deafening',false,3),(qid,'Boisterous',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to WRETCHED?', 'Wretched means miserable; content means satisfied and at ease.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Miserable',false,1),(qid,'Content',true,2),(qid,'Unhappy',false,3),(qid,'Sorrowful',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to OBFUSCATE?', 'Obfuscate means to make unclear; clarify means to make clear.', 1, 75)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Obscure',false,1),(qid,'Clarify',true,2),(qid,'Confuse',false,3),(qid,'Befog',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to REVEAL?', 'Reveal means to make known; conceal means to hide.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Expose',false,1),(qid,'Conceal',true,2),(qid,'Disclose',false,3),(qid,'Unveil',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to ASTUTE?', 'Astute means shrewd and clever; obtuse means slow to understand.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Perceptive',false,1),(qid,'Obtuse',true,2),(qid,'Shrewd',false,3),(qid,'Keen',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to WEARY?', 'Weary means tired; energetic means full of energy.', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Fatigued',false,1),(qid,'Energetic',true,2),(qid,'Exhausted',false,3),(qid,'Drowsy',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ant, 'multiple_choice', 'Which word is opposite in meaning to BIG?', 'Tiny means very small; the opposite of big.', 1, 45)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'Enormous',false,1),(qid,'Tiny',true,2),(qid,'Large',false,3),(qid,'Huge',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

END $$;

SELECT 'VR vocabulary questions inserted. Total: ' || count(*)::text AS status FROM questions q
JOIN subjects s ON q.subject_id = s.id WHERE s.code = 'VR';
