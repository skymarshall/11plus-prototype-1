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
import { OptionDisplay } from '@/components/OptionDisplay';
import { CheckCircle, XCircle, ArrowLeft, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

export default function Results() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [session, setSession] = useState<SessionWithDetails | null>(null);
  const [questions, setQuestions] = useState<QuestionWithOptions[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!sessionId || !user) {
      navigate('/dashboard');
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const subjectList = await fetchSubjects();
        if (cancelled) return;
        setSubjects(subjectList);

        const sessionData = await getSessionWithDetails(
          parseInt(sessionId),
          (id) => getSubjectById(subjectList, id)
        );
        if (cancelled) return;

        if (!sessionData || sessionData.user_id !== user.id) {
          navigate('/dashboard');
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
        if (!cancelled) console.error('Results load error:', e);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId, user, navigate]);

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

  if (isLoading || !session) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading results...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  const percentage = Math.round((session.score / session.total_questions) * 100);
  const getScoreColor = () => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <Card className="mb-8">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl">{session.subject.name} Results</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className={`text-6xl font-bold ${getScoreColor()} mb-2`}>
              {session.score}/{session.total_questions}
            </div>
            <p className="text-xl text-muted-foreground mb-6">
              {percentage}% correct
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/dashboard">
                <Button variant="outline">
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Take Another Test
                </Button>
              </Link>
              <Link to="/sessions">
                <Button variant="ghost">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  View All Sessions
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <h2 className="text-xl font-semibold mb-4">Question Review</h2>
        <div className="space-y-4">
          {questions.map((question, index) => {
            const attempt = session.attempts.find((a) => a.question_id === question.id);
            const isCorrect = attempt?.is_correct || false;
            const selectedOption = question.options.find((o) => o.id === attempt?.answer_option_id);
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
                            <XCircle className="h-5 w-5 text-red-600" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Question {index + 1}</span>
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
                      <div className="space-y-4 ml-8">
                        <div>
                          <div className="flex flex-wrap justify-center gap-4">
                            {question.options
                              .slice()
                              .sort((a, b) => a.display_order - b.display_order)
                              .map((option) => {
                                const isSelected = selectedOption?.id === option.id;
                                const isCorrectOption = option.is_correct;
                                return (
                                  <div
                                    key={option.id}
                                    className={`flex flex-col items-center rounded-lg border-2 p-3 w-44 min-h-[220px] ${
                                      isSelected && isCorrectOption
                                        ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
                                        : isSelected
                                          ? 'border-red-500 bg-red-50 dark:bg-red-950/20'
                                          : isCorrectOption
                                            ? 'border-green-500 bg-green-50/50 dark:bg-green-950/10'
                                            : 'border-border'
                                    }`}
                                  >
                                    <div className="flex-1 flex flex-col items-center justify-center min-h-0">
                                      <OptionDisplay
                                        option_text={option.option_text}
                                        option_image_url={option.option_image_url}
                                        size="large"
                                      />
                                    </div>
                                    <div className="mt-2 h-5 flex flex-col items-center justify-end text-xs font-medium flex-shrink-0">
                                      {isSelected && (
                                        <span className={isCorrectOption ? 'text-green-600' : 'text-red-600'}>
                                          Your answer
                                        </span>
                                      )}
                                      {isCorrectOption && !isSelected && (
                                        <span className="text-green-600">Correct</span>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                        </div>
                        {selectedOption == null && (
                          <p className="text-sm text-muted-foreground">Not answered</p>
                        )}
                        {question.explanation && (
                          <div className="bg-muted/50 rounded-lg p-4 mt-4">
                            <p className="text-sm font-medium text-foreground mb-1">Explanation:</p>
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
