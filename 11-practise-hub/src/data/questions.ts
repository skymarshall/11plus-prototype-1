import { supabase } from '@/lib/supabase';
import { QuestionWithOptions, AnswerOption, QuestionType } from '@/types';

interface DbQuestion {
  id: number;
  subject_id: number;
  topic_id: number | null;
  question_type: string;
  question_text: string;
  question_image_url: string | null;
  explanation: string | null;
  points: number;
  time_limit_seconds: number | null;
  is_active: boolean;
}

interface DbAnswerOption {
  id: number;
  question_id: number;
  option_text: string;
  option_image_url: string | null;
  is_correct: boolean;
  display_order: number;
}

function mapOption(row: DbAnswerOption): AnswerOption {
  return {
    id: row.id,
    question_id: row.question_id,
    option_text: row.option_text,
    option_image_url: row.option_image_url ?? undefined,
    is_correct: row.is_correct,
    display_order: row.display_order,
  };
}

function mapQuestion(row: DbQuestion, options: AnswerOption[]): QuestionWithOptions {
  return {
    id: row.id,
    subject_id: row.subject_id,
    topic_id: row.topic_id ?? undefined,
    question_type: row.question_type as QuestionType,
    question_text: row.question_text,
    question_image_url: row.question_image_url ?? undefined,
    explanation: row.explanation ?? undefined,
    points: row.points,
    time_limit_seconds: row.time_limit_seconds ?? undefined,
    is_active: row.is_active,
    options,
  };
}

export async function fetchQuestionsBySubject(subjectId: number): Promise<QuestionWithOptions[]> {
  const { data: questions, error: qError } = await supabase
    .from('questions')
    .select('*')
    .eq('subject_id', subjectId)
    .eq('is_active', true);

  if (qError) throw qError;
  if (!questions?.length) return [];

  const ids = (questions as DbQuestion[]).map((q) => q.id);
  const { data: options, error: oError } = await supabase
    .from('answer_options')
    .select('*')
    .in('question_id', ids)
    .order('display_order');

  if (oError) throw oError;

  const optionsByQuestion = (options ?? []).reduce<Record<number, AnswerOption[]>>((acc, row) => {
    const r = row as DbAnswerOption;
    if (!acc[r.question_id]) acc[r.question_id] = [];
    acc[r.question_id].push(mapOption(r));
    return acc;
  }, {});

  return (questions as DbQuestion[]).map((q) =>
    mapQuestion(q, optionsByQuestion[q.id] ?? [])
  );
}

export async function getRandomQuestions(subjectId: number, count: number = 10): Promise<QuestionWithOptions[]> {
  const all = await fetchQuestionsBySubject(subjectId);
  const shuffled = [...all].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, Math.min(count, shuffled.length));
}

export async function getQuestionById(id: number): Promise<QuestionWithOptions | null> {
  const { data: question, error: qError } = await supabase
    .from('questions')
    .select('*')
    .eq('id', id)
    .single();

  if (qError || !question) return null;

  const { data: options, error: oError } = await supabase
    .from('answer_options')
    .select('*')
    .eq('question_id', id)
    .order('display_order');

  if (oError) return mapQuestion(question as DbQuestion, []);

  const opts = (options ?? []).map((row) => mapOption(row as DbAnswerOption));
  return mapQuestion(question as DbQuestion, opts);
}

export async function getQuestionsByIds(ids: number[]): Promise<QuestionWithOptions[]> {
  if (ids.length === 0) return [];
  const { data: questions, error: qError } = await supabase
    .from('questions')
    .select('*')
    .in('id', ids);

  if (qError) throw qError;
  if (!questions?.length) return [];

  const { data: options, error: oError } = await supabase
    .from('answer_options')
    .select('*')
    .in('question_id', ids)
    .order('display_order');

  if (oError) throw oError;

  const optionsByQuestion = (options ?? []).reduce<Record<number, AnswerOption[]>>((acc, row) => {
    const r = row as DbAnswerOption;
    if (!acc[r.question_id]) acc[r.question_id] = [];
    acc[r.question_id].push(mapOption(r));
    return acc;
  }, {});

  const questionMap = (questions as DbQuestion[]).reduce<Record<number, DbQuestion>>((acc, q) => {
    acc[q.id] = q;
    return acc;
  }, {});

  return ids
    .map((id) => {
      const q = questionMap[id];
      if (!q) return null;
      return mapQuestion(q, optionsByQuestion[id] ?? []);
    })
    .filter((q): q is QuestionWithOptions => q !== null);
}
