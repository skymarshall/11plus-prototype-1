import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User as SupabaseUser, Session } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import { UserProfile } from '@/types';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (email: string, password: string, displayName: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_TIMEOUT_MS = 15000;

function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(message)), ms)
    ),
  ]);
}

function toUserProfile(supabaseUser: SupabaseUser, profile: { display_name?: string | null; avatar_url?: string | null } | null): UserProfile {
  return {
    id: supabaseUser.id,
    email: supabaseUser.email ?? '',
    display_name: profile?.display_name ?? supabaseUser.user_metadata?.full_name ?? supabaseUser.user_metadata?.name ?? supabaseUser.email?.split('@')[0] ?? 'User',
    avatar_url: profile?.avatar_url ?? undefined,
    created_at: supabaseUser.created_at,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = async (authUser: SupabaseUser): Promise<UserProfile> => {
    const { data: profile } = await supabase
      .from('profiles')
      .select('display_name, avatar_url')
      .eq('id', authUser.id)
      .single();
    return toUserProfile(authUser, profile);
  };

  useEffect(() => {
    const {
      data: { subscription },
    } =     supabase.auth.onAuthStateChange((event, session: Session | null) => {
      if (!session?.user) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      setUser(toUserProfile(session.user, null));
      setIsLoading(false);
      fetchProfile(session.user)
        .then(setUser)
        .catch(() => {});
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setUser(toUserProfile(session.user, null));
        fetchProfile(session.user).then(setUser).catch(() => {});
      }
      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const { data, error } = await withTimeout(
        supabase.auth.signInWithPassword({ email, password }),
        AUTH_TIMEOUT_MS,
        'Sign in timed out. Check that Supabase is running and your .env URL/key are correct.'
      );
      if (error) return { success: false, error: error.message };
      if (data.user) {
        setUser(toUserProfile(data.user, null));
        fetchProfile(data.user)
          .then((profile) => setUser(profile))
          .catch(() => {});
      }
      return { success: true };
    } catch (e) {
      return { success: false, error: e instanceof Error ? e.message : 'Login failed' };
    }
  };

  const signup = async (
    email: string,
    password: string,
    displayName: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const { data, error } = await withTimeout(
        supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: displayName.trim(), name: displayName.trim() },
          },
        }),
        AUTH_TIMEOUT_MS,
        'Sign up timed out. Check that Supabase is running and your .env URL/key are correct.'
      );
      if (error) return { success: false, error: error.message };

      // If we have a session, set user immediately (so redirect doesn't wait on profile).
      // Then try to load profile; new users may have profile row not visible yet (trigger delay).
      if (data.session?.user) {
        setUser(toUserProfile(data.session.user, null));
        fetchProfile(data.session.user)
          .then((profile) => setUser(profile))
          .catch(() => {});
        return { success: true };
      }

      if (data.user && !data.session) {
        return {
          success: false,
          error:
            'Please check your email to confirm your account, then sign in. (For local dev, disable email confirmation in Supabase.)',
        };
      }

      return { success: true };
    } catch (e) {
      return { success: false, error: e instanceof Error ? e.message : 'Signup failed' };
    }
  };

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  const updateProfile = async (updates: Partial<UserProfile>) => {
    if (!user) return;
    const { error } = await supabase
      .from('profiles')
      .update({
        display_name: updates.display_name ?? user.display_name,
        avatar_url: updates.avatar_url ?? user.avatar_url,
        updated_at: new Date().toISOString(),
      })
      .eq('id', user.id);
    if (!error) {
      setUser({ ...user, ...updates });
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
