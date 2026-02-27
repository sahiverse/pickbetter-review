import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../src/contexts/AuthContext';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, sendEmailVerification, fetchSignInMethodsForEmail } from 'firebase/auth';
import { auth } from '../src/firebase';

const AuthScreen: React.FC = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modeSwitched, setModeSwitched] = useState(false);

  const { signOut } = useAuth();

  const handleSubmit = async () => {
    console.log('🚀 handleSubmit called!');
    console.log('Current state:', { isSignUp, email, password });
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (isSignUp && !fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }
    
    setError(null);
    setLoading(true);

    console.log(`🔐 Attempting ${isSignUp ? 'sign up' : 'sign in'} with:`, email);

    try {
      if (isSignUp) {
        console.log('📝 Calling createUserWithEmailAndPassword...');
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        console.log('✅ Account created, sending verification email...');
        
        // Send email verification
        await sendEmailVerification(userCredential.user);
        console.log('✅ Verification email sent');
        
        setError('Account created! Please check your email and click the verification link before signing in.');
        setTimeout(() => {
          setError(null);
        }, 10000);
        
        // Don't proceed to authenticated state yet
        return;
      } else {
        console.log('🔑 Calling signInWithEmailAndPassword...');
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        
        // Check if email is verified
        if (!userCredential.user.emailVerified) {
          console.log('❌ Email not verified');
          setError('Please verify your email address before signing in. Check your email for the verification link.');
          
          // Sign out the user since they're not verified
          await auth.signOut();
          return;
        }
        
        console.log('✅ Sign in successful with verified email');
        // Get token for backend verification
        const token = await userCredential.user.getIdToken();
        console.log('Token obtained:', token.substring(0, 20) + '...');
      }
    } catch (err: any) {
      console.error('❌ Firebase error caught:', err);
      console.error('Error code:', err.code);
      console.error('Error message:', err.message);
      
      const errorCode = err.code || '';
      
      console.log('🎯 Processing Firebase error code:', errorCode);
      
      // Handle specific Firebase error codes
      if (errorCode === 'auth/user-not-found') {
        console.log('🎯 User not found detected - switching to sign up mode');
        setIsSignUp(true);
        setModeSwitched(true);
        setError(`No account found for ${email}. You can Create Account here.`);
        console.log('✅ State updated: isSignUp = true, error set');
        setTimeout(() => {
          setError(null);
          setModeSwitched(false);
          console.log('🧹 Error cleared after timeout');
        }, 5000);
      } else if (errorCode === 'auth/wrong-password') {
        console.log('🎯 Wrong password detected - staying on sign in');
        setError('Incorrect password. Please enter the correct password.');
        console.log('✅ Error set for wrong password');
      } else if (errorCode === 'auth/invalid-credential') {
        // For invalid-credential, assume user exists but wrong password
        console.log('🎯 Invalid credential - assuming wrong password');
        setError('Incorrect password. Please enter the correct password.');
      } else if (errorCode === 'auth/invalid-email') {
        setError('Please enter a valid email address.');
      } else if (errorCode === 'auth/too-many-requests') {
        setError('Too many failed attempts. Please try again later.');
      } else if (errorCode === 'auth/email-already-in-use') {
        console.log('🎯 Email already in use - switching to sign in mode');
        setIsSignUp(false);
        setModeSwitched(true);
        setError('An account already exists with this email. Please sign in instead.');
        setTimeout(() => {
          setError(null);
          setModeSwitched(false);
        }, 5000);
      } else {
        console.log('🎯 Unknown Firebase error:', errorCode, err.message);
        setError(err.message || 'Authentication failed. Please try again.');
      }
    } finally {
      setLoading(false);
      console.log('🏁 handleSubmit completed');
    }
  };

  return (
    <div className="flex flex-col h-full px-8 pt-24 pb-12 justify-between bg-[#FFFDE1]">
      
      <div className="space-y-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", damping: 12 }}
          className="w-16 h-16 bg-[#93BD57] rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-[#93BD57]/20"
        >
          <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </motion.div>

        <motion.h1
          className="text-5xl font-extrabold leading-tight text-slate-900"
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {isSignUp ? 'Join' : 'Welcome'} <br />
          <span className="text-[#93BD57]">{isSignUp ? 'Us!' : 'Back!'}</span>
        </motion.h1>

        <motion.p
          className="text-slate-500 text-lg"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {isSignUp ? 'Start your journey to better health.' : 'Scan. Evaluate. Choose Better.'}
        </motion.p>
      </div>

      <div className="space-y-4">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="bg-red-50 border-2 border-red-300 text-red-800 px-6 py-4 rounded-3xl text-sm font-bold shadow-lg"
          >
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div className="flex-1">
                {error}
              </div>
            </div>
          </motion.div>
        )}

        <div className="space-y-3">
            {isSignUp && (
              <input
                type="text"
                placeholder="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-white border-2 border-[#FBE580] rounded-2xl py-4 px-6 text-slate-900 focus:outline-none focus:border-[#93BD57] transition-all shadow-sm"
              />
            )}
            <input
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border-2 border-[#FBE580] rounded-2xl py-4 px-6 text-slate-900 focus:outline-none focus:border-[#93BD57] transition-all shadow-sm"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border-2 border-[#FBE580] rounded-2xl py-4 px-6 text-slate-900 focus:outline-none focus:border-[#93BD57] transition-all shadow-sm"
              required
              minLength={6}
            />

          <motion.button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            whileTap={{ scale: loading ? 1 : 0.95 }}
            className={`w-full font-bold py-5 rounded-2xl text-xl shadow-glow transition-all uppercase tracking-tighter ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-[#93BD57] hover:bg-[#82a84c] text-white'
            }`}
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                {isSignUp ? 'Creating Account...' : 'Signing In...'}
              </div>
            ) : (
              isSignUp ? 'Create Account' : 'Sign In'
            )}
          </motion.button>
        </div>

        <p className="text-center text-slate-400 text-sm font-bold">
          {isSignUp ? 'Already have an account?' : 'New here?'} {' '}
          <span
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
              setModeSwitched(false);
            }}
            className="text-[#93BD57] font-black cursor-pointer underline underline-offset-4"
          >
            {isSignUp ? 'Sign In' : 'Create Account'}
          </span>
        </p>
      </div>
    </div>
  );
};

export default AuthScreen;
