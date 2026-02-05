import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { AppLayout } from '@/components/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { fetchSubjects } from '@/data/subjects';
import { getRandomQuestions } from '@/data/questions';
import { createSession } from '@/services/sessionService';
import { Subject } from '@/types';
import { Play } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<number | null>(null);

  useEffect(() => {
    fetchSubjects()
      .then(setSubjects)
      .catch(() => setSubjects([]))
      .finally(() => setLoading(false));
  }, []);

  const startTest = async (subjectId: number) => {
    if (!user) return;
    setStarting(subjectId);
    try {
      const questions = await getRandomQuestions(subjectId, 10);
      if (questions.length < 10) {
        alert(`Not enough questions available for this subject. Found ${questions.length}/10.`);
        return;
      }
      const session = await createSession(user.id, subjectId);
      navigate(`/test/${session.id}`, { state: { questionIds: questions.map((q) => q.id) } });
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to start test');
    } finally {
      setStarting(null);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="container mx-auto px-4 py-8 flex justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">
            Hello, {user?.display_name?.split(' ')[0]}! 👋
          </h1>
          <p className="text-muted-foreground mt-2">
            Choose a subject area to start a 10-question practise test.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl">
          {subjects.map((subject) => (
            <Card
              key={subject.id}
              className="hover:border-primary transition-colors cursor-pointer group"
              onClick={() => !starting && startTest(subject.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="text-5xl mb-2">{subject.icon}</div>
                  <Button
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    disabled={starting === subject.id}
                  >
                    {starting === subject.id ? (
                      <span className="animate-pulse">Starting...</span>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-1" />
                        Start
                      </>
                    )}
                  </Button>
                </div>
                <CardTitle className="text-xl">{subject.name}</CardTitle>
                <CardDescription>{subject.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <span className="font-medium text-foreground">10</span> questions
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium text-foreground">~15</span> minutes
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
