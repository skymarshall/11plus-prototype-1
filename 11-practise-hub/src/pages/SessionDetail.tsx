import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { AppLayout } from '@/components/AppLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getSessionWithDetails } from '@/services/sessionService';
import { getQuestionsByIds } from '@/data/questions';
import { fetchSubjects, getSubjectById } from '@/data/subjects';
import { SessionWithDetails, QuestionWithOptions } from '@/types';
import { Subject } from '@/types';
import { MathText } from '@/components/MathText';
import { CheckCircle, XCircle, ArrowLeft, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [session, setSession] = useState<SessionWithDetails | null>(null);
  const [questions, setQuestions] = useState<QuestionWithOptions[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id || !user) {
      navigate('/sessions');
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const subjectList = await fetchSubjects();
        if (cancelled) return;
        setSubjects(subjectList);

        const sessionData = await getSessionWithDetails(
          parseInt(id),
          (subjectId) => getSubjectById(subjectList, subjectId)
        );
        if (cancelled) return;

        if (!sessionData || sessionData.user_id !== user.id) {
          navigate('/sessions');
          return;
        }
        if (!sessionData.completed_at) {
          navigate(`/test/${id}`);
          return;
        }
        setSession(sessionData);

        const questionIds = sessionData.question_ids?.length
          ? sessionData.question_ids
          : sessionData.attempts.map((a) => a.question_id);
        const loadedQuestions = await getQuestionsByIds(questionIds);
        if (cancelled) return;
        setQuestions(loadedQuestions);
      } catch (e) {
        if (!cancelled) console.error('Session detail load error:', e);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id, user, navigate]);

  const toggleQuestion = (questionId: number) => {
    setExpandedQuestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading || !session) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading session...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  const percentage = Math.round((session.score / session.total_questions) * 100);
  const getScoreColor = () => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-destructive';
  };

  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <Link
          to="/sessions"
          className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Sessions
        </Link>

        <Card className="mb-8">
          <CardHeader className="text-center pb-4">
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="text-4xl">{session.subject.icon}</span>
              <CardTitle className="text-2xl">{session.subject.name}</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              {formatDate(session.started_at)}
            </p>
          </CardHeader>
          <CardContent className="text-center">
            <div className={`text-6xl font-bold ${getScoreColor()} mb-2`}>
              {session.score}/{session.total_questions}
            </div>
            <p className="text-xl text-muted-foreground mb-6">
              {percentage}% correct
            </p>
            <Link to="/dashboard">
              <Button>
                <RotateCcw className="h-4 w-4 mr-2" />
                Take Another Test
              </Button>
            </Link>
          </CardContent>
        </Card>

        <h2 className="text-xl font-semibold mb-4">Question Review</h2>
        <div className="space-y-4">
          {questions.map((question, index) => {
            const attempt = session.attempts.find((a) => a.question_id === question.id);
            const isCorrect = attempt?.is_correct || false;
            const selectedOption = question.options.find(
              (o) => o.id === attempt?.answer_option_id
            );
            const correctOption = question.options.find((o) => o.is_correct);
            const isExpanded = expandedQuestions.has(question.id);

            return (
              <Collapsible
                key={question.id}
                open={isExpanded}
                onOpenChange={() => toggleQuestion(question.id)}
              >
                <Card className={isCorrect ? 'border-green-200' : 'border-red-200'}>
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">
                          {isCorrect ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <XCircle className="h-5 w-5 text-destructive" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">
                              Question {index + 1}
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                          <p className="font-medium text-foreground">
                            <MathText component="span">{question.question_text}</MathText>
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <CardContent className="pt-0">
                      <div className="space-y-3 ml-8">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">
                              Your answer:
                            </span>
                            <span
                              className={`font-medium ${isCorrect ? 'text-green-600' : 'text-destructive'}`}
                            >
                              {selectedOption
                                ? <MathText component="span">{selectedOption.option_text}</MathText>
                                : 'Not answered'}
                            </span>
                          </div>
                          {!isCorrect && correctOption && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-muted-foreground">
                                Correct answer:
                              </span>
                              <span className="font-medium text-green-600">
                                <MathText component="span">{correctOption.option_text}</MathText>
                              </span>
                            </div>
                          )}
                        </div>
                        {question.explanation && (
                          <div className="bg-muted/50 rounded-lg p-4 mt-4">
                            <p className="text-sm font-medium text-foreground mb-1">
                              Explanation:
                            </p>
                            <p className="text-sm text-muted-foreground">
                              <MathText component="span">{question.explanation}</MathText>
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            );
          })}
        </div>
      </div>
    </AppLayout>
  );
}
