import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { AppLayout } from '@/components/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { getUserSessionsWithDetails, deleteSession } from '@/services/sessionService';
import { fetchSubjects, getSubjectById } from '@/data/subjects';
import { SessionWithDetails } from '@/types';
import { CheckCircle, Clock, ArrowRight, Trash2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

export default function Sessions() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState<SessionWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteSessionId, setDeleteSessionId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!user) return;
    loadSessions();
  }, [user]);

  const loadSessions = () => {
    if (!user) return;
    fetchSubjects()
      .then((subjectList) =>
        getUserSessionsWithDetails(user.id, (id) => getSubjectById(subjectList, id))
      )
      .then(setSessions)
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  };

  const handleDeleteSession = async () => {
    if (!deleteSessionId) return;

    setIsDeleting(true);
    try {
      await deleteSession(deleteSessionId);
      setSessions(sessions.filter(s => s.id !== deleteSessionId));
      toast({
        title: "Session deleted",
        description: "The practice session has been removed.",
      });
    } catch (error) {
      console.error("Failed to delete session:", error);
      toast({
        title: "Error",
        description: "Failed to delete session. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
      setDeleteSessionId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getScoreColor = (score: number, total: number) => {
    const percentage = (score / total) * 100;
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-destructive';
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
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">My Sessions</h1>
            <p className="text-muted-foreground mt-1">
              View your practise history and results
            </p>
          </div>
          <Link to="/dashboard">
            <Button>Start New Test</Button>
          </Link>
        </div>

        {sessions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-4">
                You haven't completed any practise tests yet.
              </p>
              <Link to="/dashboard">
                <Button>Take Your First Test</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => {
              const isCompleted = !!session.completed_at;
              const percentage = Math.round(
                (session.score / session.total_questions) * 100
              );

              return (
                <div key={session.id} className="relative group">
                  <Link to={`/sessions/${session.id}`}>
                    <Card className="hover:border-primary transition-colors cursor-pointer">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-3xl">{session.subject.icon}</span>
                            <div>
                              <CardTitle className="text-lg">
                                {session.subject.name}
                              </CardTitle>
                              <p className="text-sm text-muted-foreground">
                                {formatDate(session.started_at)}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-muted-foreground hover:text-destructive z-10"
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setDeleteSessionId(session.id);
                              }}
                            >
                              <Trash2 className="h-5 w-5" />
                            </Button>
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-6">
                          {isCompleted ? (
                            <>
                              <div className="flex items-center gap-2">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span className="text-sm text-muted-foreground">
                                  Completed
                                </span>
                              </div>
                              <div
                                className={`font-semibold ${getScoreColor(session.score, session.total_questions)}`}
                              >
                                {session.score}/{session.total_questions} ({percentage}%)
                              </div>
                            </>
                          ) : (
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-yellow-600" />
                              <span className="text-sm text-muted-foreground">
                                In Progress
                              </span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </div>
              );
            })}
          </div>
        )}

        <AlertDialog open={!!deleteSessionId} onOpenChange={(open) => !open && setDeleteSessionId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the practice session from your history.
                Your statistical progress (if any) will be preserved.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteSession}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout >
  );
}
