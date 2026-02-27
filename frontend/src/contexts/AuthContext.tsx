// Authentication Context for React app
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged } from 'firebase/auth';
import { auth } from '../firebase';
import { authService, AuthUser } from '../services/authService';

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen to authentication state changes
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser: User | null) => {
      if (firebaseUser) {
        const authUser: AuthUser = authService.toAuthUser(firebaseUser);
        setUser(authUser);
        console.log('👤 User authenticated:', authUser.email);
      } else {
        setUser(null);
        console.log('🚪 User signed out');
      }
      setLoading(false);
    });

    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      setLoading(true);
      const tokens = await authService.signIn(email, password);
      console.log('✅ Sign in successful');

      // Store tokens in localStorage for API calls
      localStorage.setItem('firebase_token', tokens.firebaseToken);
      if (tokens.backendToken) {
        localStorage.setItem('backend_token', tokens.backendToken);
      }
    } catch (error) {
      console.error('❌ Sign in failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      setLoading(true);
      const tokens = await authService.signUp(email, password);
      console.log('✅ Sign up successful');

      // Store tokens in localStorage for API calls
      localStorage.setItem('firebase_token', tokens.firebaseToken);
      if (tokens.backendToken) {
        localStorage.setItem('backend_token', tokens.backendToken);
      }
    } catch (error) {
      console.error('❌ Sign up failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOutUser = async () => {
    try {
      setLoading(true);
      await authService.signOut();

      // Clear stored tokens
      localStorage.removeItem('firebase_token');
      localStorage.removeItem('backend_token');

      console.log('✅ Sign out successful');
    } catch (error) {
      console.error('❌ Sign out failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    signIn,
    signUp,
    signOut: signOutUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
