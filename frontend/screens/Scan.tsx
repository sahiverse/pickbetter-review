import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../src/contexts/AuthContext';

interface ScanScreenProps {
  onScanResult: (result: any) => void;
  onBack: () => void;
}

const ScanScreen: React.FC<ScanScreenProps> = ({ onScanResult, onBack }) => {
  const { getIdToken } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    startCamera();

    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' } // Use back camera
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      setError(null);
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const scanBarcode = async () => {
    if (isProcessing) return;

    setIsProcessing(true);
    setError(null);

    try {
      // For demo purposes, we'll use a mock barcode
      // In production, you'd use a barcode scanning library like QuaggaJS or ZXing
      const mockBarcode = '3017620422003'; // Example: Nutella

      console.log('📱 Scanning barcode:', mockBarcode);

      // Call the scan API
      const token = await getIdToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/products/scan/${mockBarcode}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          stopCamera();
          onScanResult({ notFound: true, barcode: mockBarcode });
          return;
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Scan result:', result);

      // Stop camera before navigating
      stopCamera();

      // Pass result to parent component
      onScanResult(result.data);

    } catch (err: any) {
      console.error('❌ Scan error:', err);
      setError(err.message || 'Failed to scan product');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualInput = async (barcode: string) => {
    if (isProcessing) return;

    setIsProcessing(true);
    setError(null);

    try {
      console.log('📱 Manual barcode input:', barcode);

      const token = await getIdToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/products/scan/${barcode}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          stopCamera();
          onScanResult({ notFound: true, barcode: barcode });
          return;
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Manual scan result:', result);

      stopCamera();
      onScanResult(result.data);

    } catch (err: any) {
      console.error('❌ Manual scan error:', err);
      setError(err.message || 'Failed to analyze product');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-full bg-[#FFFDE1] relative overflow-hidden">
      {/* Header */}
      <div className="relative z-10 p-6 pt-12">
        <div className="flex items-center justify-between mb-6">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onBack}
            className="w-12 h-12 glass rounded-2xl flex items-center justify-center border border-white/20"
          >
            <svg className="w-6 h-6 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
            </svg>
          </motion.button>

          <div className="text-center">
            <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">Scan Product</h2>
            <p className="text-[10px] font-medium text-slate-500 uppercase tracking-widest mt-1">
              Point camera at barcode
            </p>
          </div>

          <div className="w-12 h-12" /> {/* Spacer */}
        </div>
      </div>

      {/* Camera View */}
      <div className="relative px-6">
        <div className="relative bg-black rounded-3xl overflow-hidden shadow-2xl">
          <video
            ref={videoRef}
            className="w-full h-80 object-cover"
            playsInline
            muted
          />

          {/* Scanning overlay */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative">
              {/* Corner brackets */}
              <div className="absolute -top-8 -left-8 w-16 h-16 border-l-4 border-t-4 border-[#93BD57] rounded-tl-2xl"></div>
              <div className="absolute -top-8 -right-8 w-16 h-16 border-r-4 border-t-4 border-[#93BD57] rounded-tr-2xl"></div>
              <div className="absolute -bottom-8 -left-8 w-16 h-16 border-l-4 border-b-4 border-[#93BD57] rounded-bl-2xl"></div>
              <div className="absolute -bottom-8 -right-8 w-16 h-16 border-r-4 border-b-4 border-[#93BD57] rounded-br-2xl"></div>

              {/* Scanning line animation */}
              <motion.div
                className="absolute left-0 right-0 h-0.5 bg-[#93BD57] shadow-lg"
                animate={{
                  top: ['10%', '90%', '10%'],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            </div>
          </div>

          {/* Processing overlay */}
          <AnimatePresence>
            {isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/80 flex items-center justify-center"
              >
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-[#93BD57] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-white font-bold text-lg">Analyzing with AI...</p>
                  <p className="text-white/70 text-sm mt-2">Finding healthier alternatives</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 20, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            className="mx-6 mt-4 bg-red-500 border-4 border-red-400 rounded-[24px] p-4 shadow-lg"
          >
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-white mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h4 className="font-black text-white text-sm uppercase">Scan Error</h4>
                <p className="text-red-100 text-sm font-medium mt-1">{error}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Manual Input */}
      <div className="px-6 py-6">
        <div className="bg-white/60 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">
            Manual Entry
          </h3>

          <p className="text-slate-600 text-sm">
            Can't scan? Enter barcode manually for demo:
          </p>

          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter barcode (e.g., 3017620422003)"
              className="flex-1 bg-white border border-slate-200 rounded-2xl py-3 px-4 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const value = (e.target as HTMLInputElement).value.trim();
                  if (value) {
                    handleManualInput(value);
                  }
                }
              }}
            />
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                const input = document.querySelector('input[type="text"]') as HTMLInputElement;
                const value = input?.value.trim();
                if (value) {
                  handleManualInput(value);
                }
              }}
              disabled={isProcessing}
              className="bg-[#93BD57] text-white font-black px-6 py-3 rounded-2xl uppercase text-sm disabled:opacity-50"
            >
              Analyze
            </motion.button>
          </div>

          <div className="text-xs text-slate-500 space-y-1">
            <p><strong>Demo barcodes:</strong></p>
            <p>• Nutella: <code className="bg-slate-100 px-1 rounded">3017620422003</code></p>
            <p>• Coca-Cola: <code className="bg-slate-100 px-1 rounded">5449000000996</code></p>
          </div>
        </div>
      </div>

      {/* Demo Notice */}
      <div className="px-6 pb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="font-bold text-blue-900 text-sm">Demo Mode</h4>
              <p className="text-blue-700 text-sm mt-1">
                Camera scanning uses mock data. Use manual entry or demo barcodes to test Gemini AI analysis and recommendations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanScreen;
