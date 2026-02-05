import { supabase } from '@/lib/supabase';
import { PracticeSession, UserQuestionAttempt, SessionWithDetails } from '@/types';
import { Subject } from '@/types';

const SESSION_SELECT = 'id, user_id, subject_id, question_set_id, name, started_at, completed_at';

export async function getUserSessions(userId: string): Promise<PracticeSession[]> {
  const { data, error } = await supabase
    .from('practice_sessions')
    .select(SESSION_SELECT)
    .eq('user_id', userId)
    .order('started_at', { ascending: false });

  if (error) throw error;

  return (data ?? []).map((row: Record<string, unknown>) => ({
    id: row.id as number,
    user_id: row.user_id as string,
    subject_id: row.subject_id as number,
    question_set_id: row.question_set_id as number | undefined,
    name: row.name as string | undefined,
    started_at: row.started_at as string,
    completed_at: row.completed_at as string | undefined,
  }));
}

export async function getSessionById(sessionId: number): Promise<PracticeSession | null> {
  const { data, error } = await supabase
    .from('practice_sessions')
    .select(SESSION_SELECT)
    .eq('id', sessionId)
    .single();

  if (error || !data) return null;

  const row = data as Record<string, unknown>;
  return {
    id: row.id as number,
    user_id: row.user_id as string,
    subject_id: row.subject_id as number,
    question_set_id: row.question_set_id as number | undefined,
    name: row.name as string | undefined,
    started_at: row.started_at as string,
    completed_at: row.completed_at as string | undefined,
  };
}

export async function createSession(userId: string, subjectId: number): Promise<PracticeSession> {
  const { data, error } = await supabase
    .from('practice_sessions')
    .insert({
      user_id: userId,
      subject_id: subjectId,
    })
    .select(SESSION_SELECT)
    .single();

  if (error) throw error;

  const row = data as Record<string, unknown>;
  return {
    id: row.id as number,
    user_id: row.user_id as string,
    subject_id: row.subject_id as number,
    question_set_id: row.question_set_id as number | undefined,
    name: row.name as string | undefined,
    started_at: row.started_at as string,
    completed_at: row.completed_at as string | undefined,
  };
}

export async function completeSession(sessionId: number): Promise<void> {
  const { error } = await supabase
    .from('practice_sessions')
    .update({ completed_at: new Date().toISOString() })
    .eq('id', sessionId);

  if (error) throw error;
}

export async function getSessionAttempts(sessionId: number): Promise<UserQuestionAttempt[]> {
  const { data, error } = await supabase
    .from('user_question_attempts')
    .select('*')
    .eq('practice_session_id', sessionId)
    .order('created_at', { ascending: true });

  if (error) throw error;

  return (data ?? []).map((row: Record<string, unknown>) => ({
    id: row.id as number,
    user_id: row.user_id as string,
    question_id: row.question_id as number,
    practice_session_id: row.practice_session_id as number | undefined,
    answer_option_id: row.answer_option_id as number | undefined,
    answer_value: row.answer_value as string | undefined,
    is_correct: row.is_correct as boolean,
    time_taken_seconds: row.time_taken_seconds as number | undefined,
    created_at: row.created_at as string,
  }));
}

/** Saves an attempt and the order options were shown (for multiple choice). */
export async function saveAttempt(
  userId: string,
  questionId: number,
  sessionId: number,
  answerOptionId: number,
  isCorrect: boolean,
  optionDisplayOrder: number[],
  timeTakenSeconds?: number
): Promise<UserQuestionAttempt> {
  const { data, error } = await supabase
    .from('user_question_attempts')
    .insert({
      user_id: userId,
      question_id: questionId,
      practice_session_id: sessionId,
      answer_option_id: answerOptionId,
      is_correct: isCorrect,
      time_taken_seconds: timeTakenSeconds ?? null,
    })
    .select()
    .single();

  if (error) throw error;

  const attemptId = (data as Record<string, unknown>).id as number;

  for (let i = 0; i < optionDisplayOrder.length; i++) {
    const { error: orderError } = await supabase
      .from('user_question_attempt_option_order')
      .insert({
        user_question_attempt_id: attemptId,
        display_position: i + 1,
        answer_option_id: optionDisplayOrder[i],
      });
    if (orderError) throw orderError;
  }

  const row = data as Record<string, unknown>;
  return {
    id: row.id as number,
    user_id: row.user_id as string,
    question_id: row.question_id as number,
    practice_session_id: row.practice_session_id as number | undefined,
    answer_option_id: row.answer_option_id as number | undefined,
    answer_value: row.answer_value as string | undefined,
    is_correct: row.is_correct as boolean,
    time_taken_seconds: row.time_taken_seconds as number | undefined,
    created_at: row.created_at as string,
  };
}

export async function getSessionWithDetails(
  sessionId: number,
  getSubjectById: (id: number) => Subject | undefined
): Promise<SessionWithDetails | null> {
  const session = await getSessionById(sessionId);
  if (!session) return null;

  const subject = getSubjectById(session.subject_id);
  if (!subject) return null;

  const attempts = await getSessionAttempts(sessionId);
  const score = attempts.filter((a) => a.is_correct).length;
  const questionIds = attempts.map((a) => a.question_id);

  return {
    ...session,
    question_ids: questionIds.length ? questionIds : session.question_ids ?? [],
    subject,
    attempts,
    score,
    total_questions: questionIds.length || (session.question_ids?.length ?? 0),
  };
}

export async function getUserSessionsWithDetails(
  userId: string,
  getSubjectById: (id: number) => Subject | undefined
): Promise<SessionWithDetails[]> {
  const sessions = await getUserSessions(userId);

  const result: SessionWithDetails[] = [];
  for (const session of sessions) {
    const subject = getSubjectById(session.subject_id);
    if (!subject) continue;

    const attempts = await getSessionAttempts(session.id);
    const score = attempts.filter((a) => a.is_correct).length;
    const questionIds = attempts.map((a) => a.question_id);

    result.push({
      ...session,
      question_ids: questionIds.length ? questionIds : session.question_ids ?? [],
      subject,
      attempts,
      score,
      total_questions: questionIds.length || (session.question_ids?.length ?? 0),
    });
  }

  return result.sort(
    (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  );
}
