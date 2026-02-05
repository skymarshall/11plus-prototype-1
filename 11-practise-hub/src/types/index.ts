// Database types matching the SQL schema

export interface Subject {
  id: number;
  name: string;
  code: 'MATH' | 'ENG' | 'VR' | 'NVR';
  description: string;
  icon?: string;
}

export type QuestionType = 'multiple_choice' | 'free_text';

export interface Question {
  id: number;
  subject_id: number;
  topic_id?: number;
  question_type: QuestionType;
  question_text: string;
  question_image_url?: string;
  explanation?: string;
  points: number;
  time_limit_seconds?: number;
  is_active: boolean;
}

export interface AnswerOption {
  id: number;
  question_id: number;
  option_text: string;
  option_image_url?: string;
  is_correct: boolean;
  display_order: number;
}

export interface QuestionWithOptions extends Question {
  options: AnswerOption[];
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  created_at: string;
}

export interface PracticeSession {
  id: number;
  user_id: string;
  subject_id: number;
  question_set_id?: number;
  name?: string;
  started_at: string;
  completed_at?: string;
  /** Derived from attempts or from navigation state when starting a test; not stored on session in DB. */
  question_ids?: number[];
}

export interface UserQuestionAttempt {
  id: number;
  user_id: string;
  question_id: number;
  practice_session_id?: number;
  answer_option_id?: number;
  answer_value?: string;
  is_correct: boolean;
  time_taken_seconds?: number;
  created_at: string;
}

export interface SessionWithDetails extends PracticeSession {
  subject: Subject;
  attempts: UserQuestionAttempt[];
  score: number;
  total_questions: number;
}
