import { Subject } from '@/types';
import { supabase } from '@/lib/supabase';

const SUBJECT_ICONS: Record<string, string> = {
  MATH: '🔢',
  ENG: '📖',
  VR: '💬',
  NVR: '🔷',
};

export async function fetchSubjects(): Promise<Subject[]> {
  const { data, error } = await supabase
    .from('subjects')
    .select('id, name, code, description')
    .order('id');
  if (error) throw error;
  return (data ?? []).map((row) => ({
    id: row.id,
    name: row.name,
    code: row.code as Subject['code'],
    description: row.description ?? '',
    icon: SUBJECT_ICONS[row.code] ?? '📚',
  }));
}

export function getSubjectById(subjects: Subject[], id: number): Subject | undefined {
  return subjects.find((s) => s.id === id);
}

export function getSubjectByCode(subjects: Subject[], code: string): Subject | undefined {
  return subjects.find((s) => s.code === code);
}
