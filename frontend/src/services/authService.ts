/// <reference types="vite/client" />

// Authentication service for managing Firebase auth operations
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  UserCredential
} from 'firebase/auth';
import { auth } from '../firebase';

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  emailVerified: boolean;
}

export interface AuthTokens {
  firebaseToken: string;
  backendToken?: string;
}

class AuthService {
  private currentUser: User | null = null;

  constructor() {
    // Listen to authentication state changes
    onAuthStateChanged(auth, (user) => {
      this.currentUser = user;
      console.log('🔐 Auth state changed:', user ? 'Logged in' : 'Logged out');
    });
  }

  // Sign in with email and password
  async signIn(email: string, password: string): Promise<AuthTokens> {
    try {
      const userCredential: UserCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseToken = await userCredential.user.getIdToken();

      // Call backend to verify and get backend token if needed
      const backendToken = await this.verifyWithBackend(firebaseToken);

      return {
        firebaseToken,
        backendToken
      };
    } catch (error: any) {
      console.error('❌ Sign in error:', error);
      // Preserve the original Firebase error code
      const enhancedError = new Error(this.getErrorMessage(error.code));
      (enhancedError as any).code = error.code;
      (enhancedError as any).originalError = error;
      throw enhancedError;
    }
  }

  // Sign up with email and password
  async signUp(email: string, password: string): Promise<AuthTokens> {
    try {
      const userCredential: UserCredential = await createUserWithEmailAndPassword(auth, email, password);
      const firebaseToken = await userCredential.user.getIdToken();

      // Call backend to verify and get backend token if needed
      const backendToken = await this.verifyWithBackend(firebaseToken);

      return {
        firebaseToken,
        backendToken
      };
    } catch (error: any) {
      console.error('❌ Sign up error:', error);
      // Preserve the original Firebase error code
      const enhancedError = new Error(this.getErrorMessage(error.code));
      (enhancedError as any).code = error.code;
      (enhancedError as any).originalError = error;
      throw enhancedError;
    }
  }

  // Sign out
  async signOut(): Promise<void> {
    try {
      await signOut(auth);
      console.log('✅ Signed out successfully');
    } catch (error: any) {
      console.error('❌ Sign out error:', error);
      throw new Error('Failed to sign out');
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    return this.currentUser || auth.currentUser;
  }

  // Get current user's ID token
  async getIdToken(): Promise<string | null> {
    const user = this.getCurrentUser();
    if (!user) return null;

    try {
      return await user.getIdToken();
    } catch (error) {
      console.error('❌ Error getting ID token:', error);
      return null;
    }
  }

  // Verify token with backend
  private async verifyWithBackend(firebaseToken: string): Promise<string | undefined> {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${firebaseToken}`
        },
        body: JSON.stringify({ token: firebaseToken })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Backend token verification successful');
        return firebaseToken; // For now, return Firebase token
      } else {
        console.warn('⚠️  Backend verification failed, but continuing with Firebase token');
        return firebaseToken;
      }
    } catch (error) {
      console.warn('⚠️  Backend verification error, using Firebase token:', error);
      return firebaseToken;
    }
  }

  // Convert Firebase user to AuthUser
  toAuthUser(user: User): AuthUser {
    return {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      photoURL: user.photoURL,
      emailVerified: user.emailVerified
    };
  }

  // Get user-friendly error messages
  private getErrorMessage(errorCode: string): string {
    switch (errorCode) {
      case 'auth/invalid-email':
        return 'Invalid email address';
      case 'auth/user-disabled':
        return 'This account has been disabled';
      case 'auth/user-not-found':
        return 'No account found with this email';
      case 'auth/wrong-password':
        return 'Incorrect password';
      case 'auth/invalid-credential':
        return 'Invalid credentials - user not found';
      case 'auth/email-already-in-use':
        return 'An account with this email already exists';
      case 'auth/weak-password':
        return 'Password should be at least 6 characters';
      case 'auth/network-request-failed':
        return 'Network error. Please check your connection';
      case 'auth/too-many-requests':
        return 'Too many failed attempts. Please try again later';
      default:
        return 'Authentication failed. Please try again';
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
