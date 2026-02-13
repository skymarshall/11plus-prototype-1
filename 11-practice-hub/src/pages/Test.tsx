import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import {
  getSessionById,
  saveAttempt,
  completeSession,
  getSessionAttempts,
  getSessionQuestions,
} from '@/services/sessionService';
import { getQuestionsByIds } from '@/data/questions';
import { fetchSubjects, getSubjectById } from '@/data/subjects';
import { QuestionWithOptions } from '@/types';
import { Subject } from '@/types';
import { MathText } from '@/components/MathText';
import { OptionDisplay } from '@/components/OptionDisplay';
import { ArrowLeft, ArrowRight, CheckCircle, BookOpen, X } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

/** Shuffle array (Fisher–Yates). */
function shuffle<T>(arr: T[]): T[] {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export default function Test() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [questions, setQuestions] = useState<QuestionWithOptions[]>([]);
  /** For each question id: the option ids in the order shown to the user (shuffled). */
  const [optionOrderByQuestion, setOptionOrderByQuestion] = useState<Record<number, number[]>>({});
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectName, setSubjectName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  useEffect(() => {
    if (!sessionId || !user) {
      navigate('/dashboard');
      return;
    }

    let cancelled = false;

    (async () => {
      const sid = parseInt(sessionId);
      const [session, subjectList] = await Promise.all([
        getSessionById(sid),
        fetchSubjects(),
      ]);

      if (cancelled) return;
      if (!session || session.user_id !== user.id) {
        navigate('/dashboard');
        return;
      }
      if (session.completed_at) {
        navigate(`/test/${sessionId}/results`);
        return;
      }

      const subject = getSubjectById(subjectList, session.subject_id);
      if (subject) setSubjectName(subject.name);
      setSubjects(subjectList);

      const questionIds =
        (location.state as { questionIds?: number[] } | null)?.questionIds ??
        (await getSessionQuestions(sid));

      // Fallback for legacy sessions (before we started saving questions)
      if (questionIds.length === 0) {
        const attempts = await getSessionAttempts(sid);
        if (attempts.length > 0) {
          questionIds.push(...attempts.map((a) => a.question_id));
        }
      }

      if (questionIds.length === 0) {
        navigate('/dashboard');
        return;
      }

      const loadedQuestions = await getQuestionsByIds(questionIds);
      if (cancelled) return;
      const withShuffledOptions = loadedQuestions.map((q) => ({
        ...q,
        options: shuffle(q.options),
      }));
      setQuestions(withShuffledOptions);
      const orderByQ: Record<number, number[]> = {};
      withShuffledOptions.forEach((q) => {
        orderByQ[q.id] = q.options.map((o) => o.id);
      });
      setOptionOrderByQuestion(orderByQ);

      const existingAttempts = await getSessionAttempts(sid);
      const existingAnswers: Record<number, number> = {};
      existingAttempts.forEach((attempt) => {
        if (attempt.answer_option_id) {
          existingAnswers[attempt.question_id] = attempt.answer_option_id;
        }
      });
      setAnswers(existingAnswers);
      setIsLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId, user, navigate, location.state]);

  const currentQuestion = questions[currentIndex];
  const progress = questions.length ? ((currentIndex + 1) / questions.length) * 100 : 0;
  const isLastQuestion = currentIndex === questions.length - 1;
  const isAnswered = currentQuestion && answers[currentQuestion.id] !== undefined;
  const allAnswered = questions.every((q) => answers[q.id] !== undefined);

  const handleSelectAnswer = (optionId: number) => {
    if (!currentQuestion) return;
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: optionId }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleCancelTest = () => {
    setShowCancelDialog(true);
  };

  const confirmCancelTest = () => {
    setShowCancelDialog(false);
    navigate('/dashboard');
  };

  const handleSubmit = async () => {
    if (!user || !sessionId) return;
    setSubmitting(true);
    try {
      const sid = parseInt(sessionId);
      const existingAttempts = await getSessionAttempts(sid);

      for (const question of questions) {
        const selectedOptionId = answers[question.id];
        if (selectedOptionId) {
          const correctOption = question.options.find((o) => o.is_correct);
          const isCorrect = correctOption?.id === selectedOptionId;
          const alreadySaved = existingAttempts.some((a) => a.question_id === question.id);
          const displayOrder = optionOrderByQuestion[question.id] ?? question.options.map((o) => o.id);
          if (!alreadySaved) {
            await saveAttempt(
              user.id,
              question.id,
              sid,
              selectedOptionId,
              isCorrect,
              displayOrder
            );
          }
        }
      }

      await completeSession(sid);
      navigate(`/test/${sessionId}/results`);
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading test...</p>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-primary" />
              <span className="font-semibold text-foreground">{subjectName}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                Question {currentIndex + 1} of {questions.length}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancelTest}
                className="text-muted-foreground hover:text-destructive"
                disabled={submitting}
              >
                <X className="h-4 w-4 mr-1.5" />
                Cancel
              </Button>
            </div>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </header>

      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel test?</AlertDialogTitle>
            <AlertDialogDescription>
              Your progress will not be saved. You will return to the test selection page.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep going</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmCancelTest}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Cancel test
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <main className="container mx-auto px-4 py-6 max-w-3xl flex flex-col min-h-[calc(100vh-8rem)]">
        <Card>
          <CardHeader className="text-center">
            {currentQuestion.question_image_url && (
              <img
                src={currentQuestion.question_image_url}
                alt=""
                className="max-w-full max-h-48 object-contain mb-4 mx-auto"
              />
            )}
            <CardTitle className="text-xl leading-relaxed">
              <MathText component="span">{currentQuestion.question_text}</MathText>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {currentQuestion.options.some((o) => o.option_image_url) ? (
              <div className="flex flex-wrap justify-center gap-6">
                {currentQuestion.options.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => handleSelectAnswer(option.id)}
                    className={`rounded-xl border-2 p-5 cursor-pointer transition-colors flex flex-col items-center min-w-0 ${answers[currentQuestion.id] === option.id
                      ? 'border-primary bg-primary/5 ring-2 ring-primary'
                      : 'border-border hover:bg-muted/50 hover:border-muted-foreground/30'
                      }`}
                  >
                    <OptionDisplay
                      option_text={option.option_text}
                      option_image_url={option.option_image_url}
                      size="large"
                    />
                  </button>
                ))}
              </div>
            ) : (
              <RadioGroup
                value={answers[currentQuestion.id]?.toString() || ''}
                onValueChange={(value) => handleSelectAnswer(parseInt(value))}
                className="space-y-3"
              >
                {currentQuestion.options.map((option) => (
                  <div
                    key={option.id}
                    className={`flex items-center space-x-3 rounded-lg border p-4 cursor-pointer transition-colors ${answers[currentQuestion.id] === option.id
                      ? 'border-primary bg-primary/5'
                      : 'hover:bg-muted/50'
                      }`}
                    onClick={() => handleSelectAnswer(option.id)}
                  >
                    <RadioGroupItem value={option.id.toString()} id={`option-${option.id}`} />
                    <Label
                      htmlFor={`option-${option.id}`}
                      className="flex-1 cursor-pointer text-base flex items-center gap-3"
                    >
                      <OptionDisplay
                        option_text={option.option_text}
                        option_image_url={option.option_image_url}
                        size="medium"
                      />
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            )}
          </CardContent>
        </Card>

        <div className="flex-1 min-h-0" aria-hidden />

        <div className="flex items-center justify-between py-6 flex-shrink-0">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex gap-2">
            {questions.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${index === currentIndex
                  ? 'bg-primary text-primary-foreground'
                  : answers[questions[index].id] !== undefined
                    ? 'bg-primary/20 text-primary'
                    : 'bg-muted text-muted-foreground'
                  }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          {isLastQuestion ? (
            <Button onClick={handleSubmit} disabled={!allAnswered || submitting}>
              {submitting ? 'Submitting...' : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Submit
                </>
              )}
            </Button>
          ) : (
            <Button onClick={handleNext}>
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          )}
        </div>

        <div className="h-12 flex items-center justify-center flex-shrink-0">
          {isLastQuestion && !allAnswered && (
            <p className="text-center text-muted-foreground text-sm">
              Please answer all questions before submitting.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
