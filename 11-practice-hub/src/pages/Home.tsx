import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { BookOpen, CheckCircle, BarChart3, Clock } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold text-foreground">11+ Practise</span>
          </div>
          <div className="flex gap-2">
            <Link to="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link to="/signup">
              <Button>Sign up</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            Prepare for your <span className="text-primary">11+ Exam</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Practise with hundreds of questions across Mathematics, English, Verbal Reasoning, and Non-Verbal Reasoning.
          </p>
          <Link to="/signup">
            <Button size="lg" className="text-lg px-8">
              Start Practising Free
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-muted/50 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center text-foreground mb-12">
            Everything you need to succeed
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <FeatureCard
              icon={<BookOpen className="h-10 w-10" />}
              title="4 Subject Areas"
              description="Maths, English, Verbal & Non-Verbal Reasoning"
            />
            <FeatureCard
              icon={<CheckCircle className="h-10 w-10" />}
              title="10 Questions per Test"
              description="Focused practise sessions with instant feedback"
            />
            <FeatureCard
              icon={<BarChart3 className="h-10 w-10" />}
              title="Track Progress"
              description="View your history and see improvement over time"
            />
            <FeatureCard
              icon={<Clock className="h-10 w-10" />}
              title="Detailed Explanations"
              description="Learn from every question with clear explanations"
            />
          </div>
        </div>
      </section>

      {/* Subject Cards */}
      <section className="py-16 px-4">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center text-foreground mb-12">
            Four core subject areas
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <SubjectCard emoji="🔢" title="Mathematics" description="Arithmetic, reasoning & problem-solving" />
            <SubjectCard emoji="📖" title="English" description="Comprehension, grammar & vocabulary" />
            <SubjectCard emoji="💬" title="Verbal Reasoning" description="Logic, sequences & word relationships" />
            <SubjectCard emoji="🔷" title="Non-Verbal Reasoning" description="Shapes, patterns & spatial reasoning" />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary text-primary-foreground px-4">
        <div className="container mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to start practising?
          </h2>
          <p className="text-lg mb-8 opacity-90">
            Sign up now and begin your 11+ preparation journey.
          </p>
          <Link to="/signup">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              Create Free Account
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 px-4">
        <div className="container mx-auto text-center text-muted-foreground">
          <p>© {new Date().getFullYear()} 11+ Practise. Built for UK students.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="text-center p-6 rounded-lg bg-card border">
      <div className="inline-flex items-center justify-center text-primary mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
}

function SubjectCard({ emoji, title, description }: { emoji: string; title: string; description: string }) {
  return (
    <div className="p-6 rounded-lg bg-card border hover:border-primary transition-colors">
      <div className="text-4xl mb-4">{emoji}</div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
