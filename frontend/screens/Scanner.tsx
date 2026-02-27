
import React, { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library';

interface ScannerProps {
  onBarcodeDetected: (barcode: string | { notFound: true, barcode: string }) => void;
  onBack: () => void;
}

const ScannerScreen: React.FC<ScannerProps> = ({ onBarcodeDetected, onBack }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const codeReaderRef = useRef<BrowserMultiFormatReader | null>(null);
  const scannedCodesRef = useRef<Set<string>>(new Set());
  const [showManualInput, setShowManualInput] = useState(false);
  const [manualBarcode, setManualBarcode] = useState('');

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      console.log('🧹 Scanner component unmounting - cleanup');
      cleanupScanner();
    };
  }, []);

  const cleanupScanner = () => {
    console.log('🛑 Cleaning up scanner...');

    if (codeReaderRef.current) {
      try {
        codeReaderRef.current.reset();
        console.log('✅ Scanner reset');
      } catch (err) {
        console.log('⚠️ Error during cleanup:', err);
      }
      codeReaderRef.current = null;
    }

    setScanning(false);
    setInitialized(false);
    scannedCodesRef.current.clear();
  };

  const initializeScanner = async () => {
    if (!videoRef.current) {
      setError('Video element not found');
      return;
    }

    try {
      setError(null);
      console.log('🎥 Initializing ZXing barcode scanner...');

      // Create ZXing code reader
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;

      // Get video devices
      const videoInputDevices = await codeReader.listVideoInputDevices();
      console.log('📹 Available cameras:', videoInputDevices.length);

      if (videoInputDevices.length === 0) {
        throw new Error('No camera found');
      }

      // Try to find back camera
      const backCamera = videoInputDevices.find(device =>
        device.label.toLowerCase().includes('back') ||
        device.label.toLowerCase().includes('rear') ||
        device.label.toLowerCase().includes('environment')
      );

      const selectedDeviceId = backCamera?.deviceId || videoInputDevices[videoInputDevices.length - 1].deviceId;
      console.log('📸 Using camera:', backCamera?.label || videoInputDevices[videoInputDevices.length - 1].label);

      // Start decoding with improved settings
      codeReader.decodeFromVideoDevice(
        selectedDeviceId,
        videoRef.current,
        (result, error) => {
          if (result) {
            const barcode = result.getText();
            console.log('🎉 RAW BARCODE DETECTED:', barcode);
            console.log('📊 Format:', result.getBarcodeFormat());
            console.log('📍 Result points:', result.getResultPoints());

            // Prevent duplicate scans
            if (scannedCodesRef.current.has(barcode)) {
              console.log('⚠️ Duplicate scan ignored');
              return;
            }

            // Validate barcode
            if (!isValidBarcode(barcode)) {
              console.log('⚠️ Invalid barcode format, ignoring:', barcode);
              return;
            }

            console.log('✅ Valid barcode confirmed:', barcode);
            scannedCodesRef.current.add(barcode);

            // Stop scanner and navigate
            cleanupScanner();
            onBarcodeDetected(barcode);
          }

          if (error && !(error instanceof NotFoundException)) {
            // Only log actual errors, not "not found" errors
            if (error.message && !error.message.includes('No MultiFormat Readers')) {
              console.log('⚠️ Scan error:', error.message);
            }
          }
        }
      );

      console.log('✅ Scanner started successfully - ready to scan!');
      setScanning(true);
      setInitialized(true);

    } catch (err: any) {
      console.error('❌ Scanner initialization error:', err);
      setError(`Failed to start camera: ${err.message || 'Unknown error'}`);
      setInitialized(false);
      setScanning(false);
    }
  };

  const isValidBarcode = (code: string): boolean => {
    console.log('🔍 Validating barcode:', code);

    // Must be numeric and at least 6 digits
    if (!/^\d{6,}$/.test(code)) {
      console.log('❌ Invalid: Not numeric or too short');
      return false;
    }

    console.log('✅ Barcode format validation passed');
    return true;
  };

  const stopScanner = () => {
    cleanupScanner();
  };

  const restartScanner = () => {
    stopScanner();
    setTimeout(() => initializeScanner(), 500);
  };

  return (
    <div className="h-full bg-slate-900 relative overflow-hidden flex flex-col">
      {/* Glassy Interface */}
      <div className="absolute inset-0 z-10 pointer-events-none">
        <div className="h-full flex flex-col justify-between px-6 pt-12 pb-16">
          <div className="flex justify-between items-center pointer-events-auto">
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={onBack}
              className="w-12 h-12 glass rounded-2xl flex items-center justify-center border border-white/20"
            >
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
              </svg>
            </motion.button>
            <div className="glass px-4 py-2 rounded-full flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full animate-pulse shadow-[0_0_8px_#93BD57] ${scanning ? 'bg-[#93BD57]' : 'bg-gray-400'}`} />
              <span className="text-[10px] font-black text-white uppercase tracking-widest">
                {scanning ? 'Scanning' : initialized ? 'Ready' : 'Off'}
              </span>
            </div>
          </div>

          {/* Viewfinder Section with Camera Feed */}
          <div className="flex-1 flex items-center justify-center">
            <div className="relative w-80 h-80 pointer-events-none">
              {/* Camera Feed Container */}
              <div className="absolute inset-0 w-full h-full rounded-3xl overflow-hidden bg-slate-900">
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  autoPlay
                  playsInline
                  muted
                />
              </div>

              {/* Corners Overlay */}
              <div className="absolute inset-0 pointer-events-none z-10">
                <div className="absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 border-[#93BD57] rounded-tl-3xl" />
                <div className="absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 border-[#93BD57] rounded-tr-3xl" />
                <div className="absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 border-[#93BD57] rounded-bl-3xl" />
                <div className="absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 border-[#93BD57] rounded-br-3xl" />

                {/* Neon Scanning Line */}
                {scanning && (
                  <motion.div
                    animate={{ top: ['10%', '90%'] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                    className="absolute left-4 right-4 h-0.5 bg-[#93BD57] shadow-[0_0_15px_#93BD57] z-20"
                  />
                )}
              </div>
            </div>
          </div>

          <div className="space-y-8 pointer-events-auto">
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-black text-white uppercase tracking-tighter drop-shadow-xl">
                {scanning ? 'Scanning...' : initialized ? 'Camera Ready' : 'Barcode Scanner'}
              </h3>
              <p className="text-white/50 text-xs font-bold uppercase tracking-widest">
                {scanning ? 'Point camera at product barcode' : initialized ? 'Click scan to start' : 'Click start scanning to begin'}
              </p>
            </div>

            {!showManualInput ? (
              <>
                <div className="flex justify-center items-center gap-10">
                  {!initialized ? (
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={initializeScanner}
                      className="w-24 h-24 rounded-full bg-[#93BD57] p-2 shadow-2xl relative flex items-center justify-center"
                    >
                      <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </motion.button>
                  ) : (
                    <>
                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={stopScanner}
                        className="w-14 h-14 rounded-full glass border border-white/10 flex items-center justify-center text-white"
                      >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6M9 14h6" />
                        </svg>
                      </motion.button>

                      <motion.button
                        whileTap={{ scale: 0.85 }}
                        onClick={stopScanner}
                        className="w-24 h-24 rounded-full bg-red-500 p-2 shadow-2xl relative flex items-center justify-center"
                      >
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </motion.button>

                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={() => onBarcodeDetected('8902579003616')} // Test barcode
                        className="w-14 h-14 rounded-full glass border border-white/10 flex items-center justify-center text-white"
                      >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </motion.button>
                    </>
                  )}
                </div>

                <div className="flex justify-center">
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowManualInput(true)}
                    className="px-6 py-3 glass border border-white/20 rounded-full text-white text-sm font-bold uppercase tracking-widest"
                  >
                    Enter Barcode Manually
                  </motion.button>
                </div>
              </>
            ) : (
              <div className="space-y-4">
                <input
                  type="text"
                  value={manualBarcode}
                  onChange={(e) => setManualBarcode(e.target.value)}
                  placeholder="Enter barcode number"
                  className="w-full px-6 py-4 bg-white/10 border border-white/20 rounded-2xl text-white text-center text-lg font-bold placeholder-white/40 focus:outline-none focus:border-[#93BD57]"
                  autoFocus
                />
                <div className="flex gap-4">
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      if (manualBarcode.trim()) {
                        onBarcodeDetected(manualBarcode.trim());
                      }
                    }}
                    className="flex-1 px-6 py-3 bg-[#93BD57] rounded-full text-white font-bold uppercase tracking-widest"
                  >
                    Submit
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      setShowManualInput(false);
                      setManualBarcode('');
                    }}
                    className="flex-1 px-6 py-3 glass border border-white/20 rounded-full text-white font-bold uppercase tracking-widest"
                  >
                    Cancel
                  </motion.button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-red-900/90 flex flex-col items-center justify-center p-12 text-center"
          >
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-2xl font-black text-white mb-2 uppercase tracking-tighter">Camera Error</h2>
            <p className="text-white/70 font-bold text-sm uppercase tracking-widest leading-relaxed mb-6">{error}</p>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={restartScanner}
              className="px-8 py-3 bg-[#93BD57] text-white font-bold uppercase tracking-widest rounded-full"
            >
              Try Again
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ScannerScreen;
