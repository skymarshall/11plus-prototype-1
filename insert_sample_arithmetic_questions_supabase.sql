-- =====================================================
-- Sample Arithmetic Questions for Supabase (PostgreSQL)
-- 50 Multiple Choice Questions
-- =====================================================
-- Run this AFTER create_11plus_supabase.sql
-- Paste into Supabase Dashboard → SQL Editor → Run
-- =====================================================

-- Insert Mathematics subject (idempotent)
INSERT INTO subjects (name, code, description)
VALUES ('Mathematics', 'MATH', 'Mathematical reasoning, arithmetic, and problem-solving')
ON CONFLICT (code) DO NOTHING;

-- Insert topics (idempotent). Root-level: parent_topic_id NULL.
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Arithmetic', 'Basic arithmetic operations and mental maths' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Fractions', 'Working with fractions, equivalent fractions, and fraction operations' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Decimals', 'Decimal operations and conversions' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Percentages', 'Percentage calculations and applications' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Order of Operations', 'BODMAS/PEMDAS and complex calculations' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Word Problems', 'Real-world arithmetic problems' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;
INSERT INTO topics (subject_id, parent_topic_id, name, description)
SELECT id, NULL, 'Number Patterns', 'Sequences and number relationships' FROM subjects WHERE code = 'MATH'
ON CONFLICT (subject_id, parent_topic_id, name) DO NOTHING;

-- Helper: insert one question and its options. Uses topic name and subject code.
-- We use a DO block to insert all 50 questions with local variables.
DO $$
DECLARE
  sid INT;
  t_ar INT; t_fr INT; t_de INT; t_pe INT; t_oo INT; t_wp INT; t_pa INT;
  qid INT;
BEGIN
  SELECT id INTO sid FROM subjects WHERE code = 'MATH';
  SELECT id INTO t_ar FROM topics WHERE subject_id = sid AND name = 'Arithmetic' AND parent_topic_id IS NULL;
  SELECT id INTO t_fr FROM topics WHERE subject_id = sid AND name = 'Fractions' AND parent_topic_id IS NULL;
  SELECT id INTO t_de FROM topics WHERE subject_id = sid AND name = 'Decimals' AND parent_topic_id IS NULL;
  SELECT id INTO t_pe FROM topics WHERE subject_id = sid AND name = 'Percentages' AND parent_topic_id IS NULL;
  SELECT id INTO t_oo FROM topics WHERE subject_id = sid AND name = 'Order of Operations' AND parent_topic_id IS NULL;
  SELECT id INTO t_wp FROM topics WHERE subject_id = sid AND name = 'Word Problems' AND parent_topic_id IS NULL;
  SELECT id INTO t_pa FROM topics WHERE subject_id = sid AND name = 'Number Patterns' AND parent_topic_id IS NULL;

  -- Q1
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is the value of \( 24 \times 3 + 18 \div 2 - 15 \)?', 'First calculate: \( 24 \times 3 = 72 \), \( 18 \div 2 = 9 \). Then: \( 72 + 9 - 15 = 66 \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'60',false,1),(qid,'66',true,2),(qid,'72',false,3),(qid,'81',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q2
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{3}{4} + \frac{2}{5} \)?', 'Find common denominator: \( \frac{3}{4} = \frac{15}{20} \), \( \frac{2}{5} = \frac{8}{20} \). Sum = \( \frac{23}{20} = 1\frac{3}{20} \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'\( \frac{5}{9} \)',false,1),(qid,'\( \frac{23}{20} \)',true,2),(qid,'\( 1\frac{1}{4} \)',false,3),(qid,'\( 1\frac{1}{5} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q3
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'A shirt costs £45. If it is reduced by 20%, then increased by 10%, what is the final price?', 'First reduction: \( 45 \times 0.8 = 36 \). Then increase: \( 36 \times 1.1 = 39.60 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'£39.60',true,1),(qid,'£40.50',false,2),(qid,'£41.40',false,3),(qid,'£42.00',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q4
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( 8 + 4 \times 3 - 12 \div 2 \)?', 'Follow BODMAS: \( 4 \times 3 = 12 \), \( 12 \div 2 = 6 \). Then: \( 8 + 12 - 6 = 14 \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'10',false,1),(qid,'14',true,2),(qid,'18',false,3),(qid,'20',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q5
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'Emma has 3 times as many stickers as Tom. If Tom has 24 stickers, and they share 18 stickers equally with Sarah, how many stickers does Sarah get?', 'They share 18 stickers equally: \( 18 \div 3 = 6 \)', 1, 150)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'6',true,1),(qid,'8',false,2),(qid,'12',false,3),(qid,'18',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q6
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is \( 2.5 \times 3.6 \)?', '\( 2.5 \times 3.6 = 9.0 \)', 1, 60)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'8.5',false,1),(qid,'9.0',true,2),(qid,'9.5',false,3),(qid,'10.0',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q7
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'If \( \frac{3}{8} \) of a number is 27, what is \( \frac{5}{6} \) of that number?', 'If \( \frac{3}{8} = 27 \), then the number is \( 27 \div \frac{3}{8} = 72 \). So \( \frac{5}{6} \times 72 = 60 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'45',false,1),(qid,'54',false,2),(qid,'60',true,3),(qid,'72',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q8
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pa, 'multiple_choice', 'What is the next number in this sequence: 2, 6, 12, 20, 30, ?', 'Pattern: differences are 4, 6, 8, 10. Next difference is 12, so \( 30 + 12 = 42 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'40',false,1),(qid,'42',true,2),(qid,'44',false,3),(qid,'48',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q9
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'Calculate: \( (15^2 - 12^2) \div 3 \)', '\( 15^2 = 225 \), \( 12^2 = 144 \). So \( 225 - 144 = 81 \). Then \( 81 \div 3 = 27 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'9',false,1),(qid,'18',false,2),(qid,'27',true,3),(qid,'36',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q10
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'In a class of 30 students, 40% are girls. If 5 more girls join the class, what percentage of the class are now girls?', 'Original: 12 girls, 18 boys. After: 17 girls, total = 35. \( \frac{17}{35} \approx 48.6\% \)', 1, 150)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'45%',false,1),(qid,'48.6%',true,2),(qid,'50%',false,3),(qid,'52%',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q11–50: same pattern (abbreviated for length; you can duplicate the 3-line pattern per question)
  -- Q11
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( 1\frac{2}{3} + 2\frac{1}{4} \)?', '\( 1\frac{2}{3} = \frac{5}{3} = \frac{20}{12} \), \( 2\frac{1}{4} = \frac{9}{4} = \frac{27}{12} \). Sum = \( \frac{47}{12} = 3\frac{11}{12} \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'\( 3\frac{3}{7} \)',false,1),(qid,'\( 3\frac{11}{12} \)',true,2),(qid,'\( 4\frac{1}{12} \)',false,3),(qid,'\( 4\frac{1}{3} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q12
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is \( 4.8 \div 0.12 \)?', '\( 4.8 \div 0.12 = 40 \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'36',false,1),(qid,'40',true,2),(qid,'44',false,3),(qid,'48',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q13
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( 6 \times (8 - 3) + 4^2 \div 2 \)?', 'Brackets: \( 8 - 3 = 5 \). Then: \( 6 \times 5 = 30 \), \( 4^2 \div 2 = 8 \). Final: \( 30 + 8 = 38 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'34',false,1),(qid,'38',true,2),(qid,'42',false,3),(qid,'46',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q14
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'A train travels 240 km in 3 hours. How far will it travel in 5 hours at the same speed?', 'Speed = \( 240 \div 3 = 80 \) km/h. Distance = \( 80 \times 5 = 400 \) km', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'360 km',false,1),(qid,'400 km',true,2),(qid,'420 km',false,3),(qid,'480 km',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q15
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{2}{3} \) of \( \frac{4}{5} \)?', '\( \frac{2}{3} \times \frac{4}{5} = \frac{8}{15} \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'\( \frac{6}{8} \)',false,1),(qid,'\( \frac{8}{15} \)',true,2),(qid,'\( \frac{6}{15} \)',false,3),(qid,'\( \frac{8}{8} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q16
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is the sum of all prime numbers between 10 and 20?', 'Primes: 11, 13, 17, 19. Sum = 60', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'50',false,1),(qid,'60',true,2),(qid,'70',false,3),(qid,'80',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q17
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'A book costs £12. After a 15% discount, what is the new price?', 'Discount = \( 12 \times 0.15 = 1.80 \). New price = \( 12 - 1.80 = 10.20 \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'£9.80',false,1),(qid,'£10.20',true,2),(qid,'£10.50',false,3),(qid,'£10.80',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q18
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pa, 'multiple_choice', 'What is the 8th term in this sequence: 5, 11, 17, 23, ...?', 'Adding 6 each time. 8th term = \( 5 + 7 \times 6 = 47 \)', 1, 120)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'41',false,1),(qid,'47',true,2),(qid,'53',false,3),(qid,'59',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q19
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is 0.375 as a fraction in its simplest form?', '\( 0.375 = \frac{3}{8} \)', 1, 90)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'\( \frac{3}{8} \)',true,1),(qid,'\( \frac{375}{1000} \)',false,2),(qid,'\( \frac{1}{3} \)',false,3),(qid,'\( \frac{3}{10} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q20
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'Three friends share some money. Alice gets \( \frac{2}{5} \), Ben gets \( \frac{1}{3} \), Charlie gets the rest. If Charlie gets £24, how much money did they share?', 'Charlie gets \( \frac{4}{15} \). If \( \frac{4}{15} = 24 \), total = \( 24 \div \frac{4}{15} = 90 \)', 1, 150)
  RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES
    (qid,'£72',false,1),(qid,'£90',true,2),(qid,'£96',false,3),(qid,'£108',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  -- Q21–Q50
  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is \( 144 \div 12 \times 3 - 18 \)?', '\( 144 \div 12 = 12 \), \( 12 \times 3 = 36 \), \( 36 - 18 = 18 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'12',false,1),(qid,'18',true,2),(qid,'24',false,3),(qid,'30',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{5}{6} - \frac{3}{8} \)?', 'Common denominator: \( \frac{5}{6} = \frac{20}{24} \), \( \frac{3}{8} = \frac{9}{24} \). Difference = \( \frac{11}{24} \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( \frac{1}{4} \)',false,1),(qid,'\( \frac{11}{24} \)',true,2),(qid,'\( \frac{2}{14} \)',false,3),(qid,'\( \frac{1}{2} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'If 25% of a number is 15, what is 75% of that number?', 'If 25% = 15, then the number is \( 15 \div 0.25 = 60 \). So 75% × 60 = 45', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'30',false,1),(qid,'45',true,2),(qid,'50',false,3),(qid,'60',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( (10 + 5) \times 2 - 8 \div 4 \)?', 'Brackets: \( 10 + 5 = 15 \). Then: \( 15 \times 2 = 30 \), \( 8 \div 4 = 2 \). Final: \( 30 - 2 = 28 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'26',false,1),(qid,'28',true,2),(qid,'32',false,3),(qid,'34',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'A rectangle has length 8 cm and width 5 cm. What is the area?', 'Area = \( 8 \times 5 = 40 \) cm²', 1, 60) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'26 cm²',false,1),(qid,'40 cm²',true,2),(qid,'45 cm²',false,3),(qid,'50 cm²',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is \( 7.2 \times 0.5 \)?', '\( 7.2 \times 0.5 = 3.6 \)', 1, 60) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'3.5',false,1),(qid,'3.6',true,2),(qid,'3.7',false,3),(qid,'4.0',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{3}{4} \div \frac{1}{2} \)?', '\( \frac{3}{4} \div \frac{1}{2} = \frac{3}{4} \times \frac{2}{1} = \frac{6}{4} = 1\frac{1}{2} \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( \frac{1}{2} \)',false,1),(qid,'\( \frac{3}{4} \)',false,2),(qid,'\( 1\frac{1}{2} \)',true,3),(qid,'2',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pa, 'multiple_choice', 'What is the missing number: 3, 9, 27, 81, ?', 'Multiplying by 3 each time. \( 81 \times 3 = 243 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'162',false,1),(qid,'243',true,2),(qid,'324',false,3),(qid,'405',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is \( 17 \times 13 \)?', '\( 17 \times 13 = 221 \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'211',false,1),(qid,'221',true,2),(qid,'231',false,3),(qid,'241',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'A test has 40 questions. If Sarah got 85% correct, how many did she get wrong?', 'Correct: \( 40 \times 0.85 = 34 \). Wrong = \( 40 - 34 = 6 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'4',false,1),(qid,'6',true,2),(qid,'8',false,3),(qid,'10',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{1}{3} + \frac{1}{4} + \frac{1}{6} \)?', 'Common denominator 12. \( \frac{4}{12} + \frac{3}{12} + \frac{2}{12} = \frac{9}{12} = \frac{3}{4} \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( \frac{3}{13} \)',false,1),(qid,'\( \frac{3}{4} \)',true,2),(qid,'1',false,3),(qid,'\( \frac{9}{12} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( 2^3 + 3^2 - 4 \)?', '\( 2^3 = 8 \), \( 3^2 = 9 \). So \( 8 + 9 - 4 = 13 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'11',false,1),(qid,'13',true,2),(qid,'15',false,3),(qid,'17',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'Tom is 3 years older than Lucy. In 5 years, Tom will be twice as old as Lucy is now. How old is Lucy now?', 'Let Lucy = \( x \). In 5 years Tom = \( x + 8 = 2x \), so \( x = 8 \)', 1, 180) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'6',false,1),(qid,'8',true,2),(qid,'10',false,3),(qid,'11',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is \( 0.6 \times 0.25 \)?', '\( 0.6 \times 0.25 = 0.15 \)', 1, 60) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'0.10',false,1),(qid,'0.15',true,2),(qid,'0.20',false,3),(qid,'0.25',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is the greatest common factor (GCF) of 24 and 36?', 'GCF = 12', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'6',false,1),(qid,'12',true,2),(qid,'18',false,3),(qid,'24',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'A shop increases all prices by 20%. If an item now costs £36, what was its original price?', 'Original = \( 36 \div 1.2 = 30 \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'£28',false,1),(qid,'£30',true,2),(qid,'£32',false,3),(qid,'£34',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( 4\frac{1}{2} - 2\frac{3}{4} \)?', '\( 4\frac{1}{2} = \frac{18}{4} \), \( 2\frac{3}{4} = \frac{11}{4} \). Difference = \( \frac{7}{4} = 1\frac{3}{4} \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( 1\frac{1}{4} \)',false,1),(qid,'\( 1\frac{3}{4} \)',true,2),(qid,'2',false,3),(qid,'\( 2\frac{1}{4} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pa, 'multiple_choice', 'What is the next number: 1, 4, 9, 16, 25, ?', 'Square numbers. Next is \( 6^2 = 36 \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'30',false,1),(qid,'36',true,2),(qid,'40',false,3),(qid,'49',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'A recipe needs 2.5 cups of flour for 10 servings. How much flour is needed for 16 servings?', '\( 2.5 \div 10 = 0.25 \) cups per serving. For 16: \( 0.25 \times 16 = 4 \) cups', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'3.5 cups',false,1),(qid,'4 cups',true,2),(qid,'4.5 cups',false,3),(qid,'5 cups',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is the least common multiple (LCM) of 6 and 8?', 'LCM = 24', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'12',false,1),(qid,'24',true,2),(qid,'32',false,3),(qid,'48',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( 100 - 4 \times (8 + 2) \div 2 \)?', 'Brackets: \( 8 + 2 = 10 \). Then: \( 4 \times 10 = 40 \), \( 40 \div 2 = 20 \). Final: \( 100 - 20 = 80 \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'70',false,1),(qid,'80',true,2),(qid,'90',false,3),(qid,'100',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{2}{3} \) of \( \frac{3}{4} \)?', '\( \frac{2}{3} \times \frac{3}{4} = \frac{6}{12} = \frac{1}{2} \)', 1, 90) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( \frac{1}{3} \)',false,1),(qid,'\( \frac{1}{2} \)',true,2),(qid,'\( \frac{2}{3} \)',false,3),(qid,'\( \frac{5}{7} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pe, 'multiple_choice', 'If a number is increased by 25% and then decreased by 20%, what is the overall percentage change?', '\( 100 \times 1.25 = 125 \), \( 125 \times 0.8 = 100 \). No change = 0%', 1, 150) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'-5%',false,1),(qid,'0%',true,2),(qid,'+5%',false,3),(qid,'+10%',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_de, 'multiple_choice', 'What is 1.25 as a fraction?', '\( 1.25 = \frac{5}{4} = 1\frac{1}{4} \)', 1, 60) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( 1\frac{1}{4} \)',true,1),(qid,'\( 1\frac{1}{2} \)',false,2),(qid,'\( \frac{5}{4} \)',true,3),(qid,'\( \frac{125}{100} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true LIMIT 1;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'A bag contains red and blue marbles. If \( \frac{3}{5} \) are red and there are 24 red marbles, how many blue marbles are there?', 'Total = \( 24 \div \frac{3}{5} = 40 \). Blue = \( 40 - 24 = 16 \)', 1, 150) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'12',false,1),(qid,'16',true,2),(qid,'20',false,3),(qid,'24',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_ar, 'multiple_choice', 'What is \( 256 \div 16 \)?', '\( 256 \div 16 = 16 \)', 1, 60) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'14',false,1),(qid,'16',true,2),(qid,'18',false,3),(qid,'20',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_pa, 'multiple_choice', 'What is the 10th term: 2, 5, 8, 11, ...?', 'Adding 3 each time. 10th term = \( 2 + 9 \times 3 = 29 \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'26',false,1),(qid,'29',true,2),(qid,'32',false,3),(qid,'35',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_fr, 'multiple_choice', 'What is \( \frac{5}{8} + \frac{3}{4} \)?', '\( \frac{5}{8} + \frac{6}{8} = \frac{11}{8} = 1\frac{3}{8} \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'\( 1\frac{1}{8} \)',false,1),(qid,'\( 1\frac{3}{8} \)',true,2),(qid,'\( \frac{8}{12} \)',false,3),(qid,'\( 1\frac{1}{2} \)',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_oo, 'multiple_choice', 'What is \( 3 \times (12 - 4) + 18 \div 3 \)?', 'Brackets: \( 12 - 4 = 8 \). Then: \( 3 \times 8 = 24 \), \( 18 \div 3 = 6 \). Final: \( 24 + 6 = 30 \)', 1, 120) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'26',false,1),(qid,'30',true,2),(qid,'34',false,3),(qid,'38',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

  INSERT INTO questions (subject_id, topic_id, question_type, question_text, explanation, points, time_limit_seconds)
  VALUES (sid, t_wp, 'multiple_choice', 'Jack has £50. He spends \( \frac{2}{5} \) on books and \( \frac{1}{4} \) of the remainder on pens. How much does he have left?', 'Books: \( 50 \times \frac{2}{5} = 20 \). Remainder: \( 50 - 20 = 30 \). Pens: \( 30 \times \frac{1}{4} = 7.50 \). Left: \( 30 - 7.50 = 22.50 \)', 1, 180) RETURNING id INTO qid;
  INSERT INTO answer_options (question_id, option_text, is_correct, display_order) VALUES (qid,'£20.00',false,1),(qid,'£22.50',true,2),(qid,'£25.00',false,3),(qid,'£27.50',false,4);
  INSERT INTO correct_answers (question_id, answer_type, answer_value) SELECT qid, 'option_id'::answer_type_enum, id::text FROM answer_options WHERE question_id = qid AND is_correct = true;

END $$;

SELECT 'Sample questions inserted. Total: ' || count(*)::text AS status FROM questions q
JOIN subjects s ON q.subject_id = s.id WHERE s.code = 'MATH';
