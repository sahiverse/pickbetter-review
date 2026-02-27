// Firebase configuration for PickBetter frontend
import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getAnalytics } from 'firebase/analytics';

// Check if Firebase config is available
const hasFirebaseConfig = import.meta.env.VITE_FIREBASE_API_KEY &&
                         import.meta.env.VITE_FIREBASE_PROJECT_ID &&
                         import.meta.env.VITE_FIREBASE_API_KEY !== 'your_firebase_api_key_here';

let app;
let auth;
let analytics;

if (hasFirebaseConfig) {
  // Firebase configuration
  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
  };

  // Initialize Firebase
  app = initializeApp(firebaseConfig);

  // Initialize Firebase Authentication and get a reference to the service
  auth = getAuth(app);

  // Initialize Analytics (only in production)
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    analytics = getAnalytics(app);
  }

  // Connect to emulators in development
  if (import.meta.env.DEV && import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true') {
    try {
      connectAuthEmulator(auth, "http://localhost:9099");
      console.log('🔗 Connected to Firebase Auth Emulator');
    } catch (error) {
      console.warn('⚠️  Firebase Auth Emulator connection failed:', error);
    }
  }

  console.log('✅ Firebase initialized successfully');
} else {
  console.warn('⚠️  Firebase config not found. Running in demo mode.');
  console.log('   To enable real authentication, add Firebase config to frontend/.env.local');

  // Create mock Firebase objects for demo mode
  auth = {
    currentUser: null,
    signInWithEmailAndPassword: async () => {
      throw new Error('Firebase not configured. Add Firebase config to enable authentication.');
    },
    createUserWithEmailAndPassword: async () => {
      throw new Error('Firebase not configured. Add Firebase config to enable authentication.');
    },
    signOut: async () => {
      console.log('Demo mode: Sign out called');
    },
    onAuthStateChanged: (callback) => {
      callback(null); // Always unauthenticated in demo mode
      return () => {}; // Mock unsubscribe
    }
  };

  app = {}; // Mock app object
}

export { analytics };
export { app };
export { auth };
export default app;
