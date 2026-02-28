import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ContributionScreenProps {
  barcode: string;
  onBack: () => void;
  onContributionSuccess: (result: any) => void;
}

type ImageType = 'nutrition' | 'ingredients';
type CaptureMode = 'select' | 'camera' | 'gallery';

// Camera Capture Component
const CameraCapture: React.FC<{
  onCapture: (file: File, preview: string) => void;
  onCancel: () => void;
  imageType: ImageType;
}> = ({ onCapture, onCancel, imageType }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  React.useEffect(() => {
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false
        });
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      } catch (err: any) {
        console.error('Camera error:', err);
        setError(err.message || 'Could not access camera');
      }
    };

    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const handleVideoReady = () => {
    setIsReady(true);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current || !stream) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const fileName = `${imageType}_capture_${Date.now()}.jpg`;
        const file = new File([blob], fileName, { type: 'image/jpeg' });
        const preview = canvas.toDataURL('image/jpeg');
        onCapture(file, preview);
      }
    }, 'image/jpeg', 0.9);

    stream.getTracks().forEach(track => track.stop());
  };

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      <div className="px-4 py-3 flex items-center justify-between bg-black/80">
        <button onClick={onCancel} className="text-white font-medium flex items-center gap-2">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Cancel
        </button>
        <span className="text-white font-medium">
          {imageType === 'nutrition' ? 'Nutrition Label' : 'Ingredients'}
        </span>
        <div className="w-16" />
      </div>

      {error && (
        <div className="flex-1 flex flex-col items-center justify-center p-6">
          <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-white text-center mb-4">{error}</p>
          <button onClick={onCancel} className="px-6 py-3 bg-[#93BD57] text-white rounded-full font-medium">
            Go Back
          </button>
        </div>
      )}

      {!error && (
        <>
          <div className="flex-1 relative overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              onLoadedMetadata={handleVideoReady}
              className="absolute inset-0 w-full h-full object-cover"
            />
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-8 border-2 border-white/50 rounded-2xl">
                <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-[#93BD57] rounded-tl-xl" />
                <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-[#93BD57] rounded-tr-xl" />
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-[#93BD57] rounded-bl-xl" />
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-[#93BD57] rounded-br-xl" />
              </div>
              <p className="absolute bottom-20 left-0 right-0 text-center text-white/80 text-sm font-medium">
                Align the {imageType === 'nutrition' ? 'nutrition label' : 'ingredients list'} within the frame
              </p>
            </div>
          </div>

          <div className="p-6 bg-black flex justify-center">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={capturePhoto}
              disabled={!isReady}
              className="w-20 h-20 rounded-full border-4 border-white bg-[#93BD57] disabled:opacity-50 flex items-center justify-center"
            >
              <div className="w-14 h-14 rounded-full bg-white" />
            </motion.button>
          </div>
        </>
      )}

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
};

const ContributionScreen: React.FC<ContributionScreenProps> = ({
  barcode,
  onBack,
  onContributionSuccess
}) => {
  const [step, setStep] = useState<'intro' | 'upload' | 'preview' | 'submitting' | 'success' | 'error'>('intro');
  const [nutritionImage, setNutritionImage] = useState<File | null>(null);
  const [ingredientsImage, setIngredientsImage] = useState<File | null>(null);
  const [nutritionPreview, setNutritionPreview] = useState<string | null>(null);
  const [ingredientsPreview, setIngredientsPreview] = useState<string | null>(null);
  const [productName, setProductName] = useState('');
  const [brand, setBrand] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Camera capture state
  const [activeCamera, setActiveCamera] = useState<ImageType | null>(null);
  const [showModeSelector, setShowModeSelector] = useState<ImageType | null>(null);

  const nutritionInputRef = useRef<HTMLInputElement>(null);
  const ingredientsInputRef = useRef<HTMLInputElement>(null);

  const handleNutritionImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setNutritionImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setNutritionPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleIngredientsImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIngredientsImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setIngredientsPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleCameraCapture = useCallback((file: File, preview: string) => {
    if (activeCamera === 'nutrition') {
      setNutritionImage(file);
      setNutritionPreview(preview);
    } else if (activeCamera === 'ingredients') {
      setIngredientsImage(file);
      setIngredientsPreview(preview);
    }
    setActiveCamera(null);
    setShowModeSelector(null);
  }, [activeCamera]);

  const handleCaptureCancel = () => {
    setActiveCamera(null);
    setShowModeSelector(null);
  };

  const handleModeSelect = (mode: CaptureMode, type: ImageType) => {
    if (mode === 'camera') {
      setActiveCamera(type);
      setShowModeSelector(null);
    } else if (mode === 'gallery') {
      if (type === 'nutrition') {
        document.getElementById('nutrition-file-input')?.click();
      } else {
        document.getElementById('ingredients-file-input')?.click();
      }
      setShowModeSelector(null);
    }
  };

  const handleSubmit = async () => {
    if (!nutritionImage) return;

    setStep('submitting');
    setError(null);

    try {
      const formData = new FormData();
      formData.append('barcode', barcode);
      formData.append('nutrition_image', nutritionImage);
      if (ingredientsImage) {
        formData.append('ingredients_image', ingredientsImage);
      }
      if (productName.trim()) {
        formData.append('product_name', productName.trim());
      }
      if (brand.trim()) {
        formData.append('brand', brand.trim());
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/contribute/`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // If we hit a 429 Rate Limit from Gemini during contribution parsing,
      // we should still show the user the success screen to thank them, 
      // rather than showing a scary quota error string.
      if (!response.ok && response.status !== 429) {
        throw new Error(data.detail || 'Failed to submit contribution');
      }

      setResult(data);
      setStep('success');
      onContributionSuccess(data);
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.');
      setStep('error');
    }
  };

  // Mode Selector Modal
  const ModeSelectorModal: React.FC<{
    type: ImageType;
    onClose: () => void;
  }> = ({ type, onClose }) => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 z-50 flex items-end"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        className="w-full bg-white rounded-t-3xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-12 h-1 bg-slate-300 rounded-full mx-auto mb-6" />

        <h3 className="text-xl font-black text-slate-900 mb-6 uppercase tracking-tighter">
          {type === 'nutrition' ? 'Add Nutrition Label' : 'Add Ingredients List'}
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => handleModeSelect('camera', type)}
            className="p-6 rounded-2xl border-2 border-[#93BD57] bg-[#93BD57]/5 flex flex-col items-center gap-3 hover:bg-[#93BD57]/10 transition-colors"
          >
            <div className="w-16 h-16 rounded-full bg-[#93BD57] flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span className="font-bold text-slate-700 uppercase tracking-wider">Camera</span>
            <span className="text-xs text-slate-500">Take a photo</span>
          </button>

          <button
            onClick={() => handleModeSelect('gallery', type)}
            className="p-6 rounded-2xl border-2 border-slate-200 flex flex-col items-center gap-3 hover:border-[#93BD57] hover:bg-[#93BD57]/5 transition-colors"
          >
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="font-bold text-slate-500 uppercase tracking-wider">Gallery</span>
            <span className="text-xs text-slate-400">Choose from library</span>
          </button>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 py-3 text-slate-500 font-bold uppercase tracking-widest"
        >
          Cancel
        </button>
      </motion.div>
    </motion.div>
  );

  // Intro Screen - Friendly message when product not found
  if (step === 'intro') {
    return (
      <div className="h-full bg-[#FFFDE1] flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="w-24 h-24 mx-auto mb-6 bg-[#93BD57] rounded-full flex items-center justify-center">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>

          <h2 className="text-3xl font-black text-slate-900 mb-4 uppercase tracking-tighter">
            Product Not Found
          </h2>

          <p className="text-slate-600 mb-2 font-medium">
            We couldn't find barcode <span className="font-bold text-[#93BD57]">{barcode}</span> in our database.
          </p>

          <p className="text-slate-500 text-sm mb-8">
            But here's the good news! You can help us grow by contributing this product.
            Just snap photos of the nutrition label and ingredients list!
          </p>

          <div className="space-y-3">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setStep('upload')}
              className="w-full py-4 bg-[#93BD57] text-white font-bold uppercase tracking-widest rounded-full shadow-lg"
            >
              Contribute This Product
            </motion.button>

            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={onBack}
              className="w-full py-3 text-slate-500 font-bold uppercase tracking-widest"
            >
              Go Back
            </motion.button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Upload Screen - Image selection
  if (step === 'upload' || step === 'preview') {
    return (
      <div className="h-full bg-[#FFFDE1] flex flex-col">
        {/* Camera Capture Overlay */}
        <AnimatePresence>
          {activeCamera && (
            <CameraCapture
              key="camera"
              onCapture={handleCameraCapture}
              onCancel={handleCaptureCancel}
              imageType={activeCamera}
            />
          )}
        </AnimatePresence>

        {/* Mode Selector Modal */}
        <AnimatePresence>
          {showModeSelector && (
            <ModeSelectorModal
              type={showModeSelector}
              onClose={() => setShowModeSelector(null)}
            />
          )}
        </AnimatePresence>

        {/* Header */}
        <div className="px-6 pt-12 pb-4 flex items-center justify-between">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => step === 'upload' ? setStep('intro') : setStep('upload')}
            className="w-12 h-12 glass rounded-2xl flex items-center justify-center border border-slate-200"
          >
            <svg className="w-6 h-6 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
            </svg>
          </motion.button>

          <div className="glass px-4 py-2 rounded-full flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#93BD57] animate-pulse shadow-[0_0_8px_#93BD57]" />
            <span className="text-[10px] font-black text-slate-700 uppercase tracking-widest">
              Step {nutritionImage ? '2' : '1'} of 2
            </span>
          </div>
        </div>

        <div className="flex-1 px-6 pb-6 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h2 className="text-2xl font-black text-slate-900 mb-2 uppercase tracking-tighter">
              Add Photos
            </h2>
            <p className="text-slate-500 text-sm mb-6">
              Take photos or upload from gallery
            </p>

            {/* Nutrition Image Upload */}
            <div className="mb-6">
              <label className="block text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">
                Nutrition Facts Label *
              </label>

              {nutritionPreview ? (
                <div className="relative rounded-2xl overflow-hidden border-2 border-[#93BD57]">
                  <img
                    src={nutritionPreview}
                    alt="Nutrition preview"
                    className="w-full h-48 object-cover"
                  />
                  <button
                    onClick={() => {
                      setNutritionImage(null);
                      setNutritionPreview(null);
                    }}
                    className="absolute top-2 right-2 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowModeSelector('nutrition')}
                  className="w-full h-48 rounded-2xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center gap-3 hover:border-[#93BD57] hover:bg-[#93BD57]/5 transition-colors"
                >
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <span className="text-slate-700 font-bold block">Tap to add photo</span>
                    <span className="text-slate-400 text-sm">Camera or Gallery</span>
                  </div>
                </button>
              )}
              {/* Hidden file input for gallery option */}
              <input
                id="nutrition-file-input"
                type="file"
                accept="image/*"
                onChange={handleNutritionImageSelect}
                className="hidden"
              />
            </div>

            {/* Ingredients Image Upload */}
            <div className="mb-6">
              <label className="block text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">
                Ingredients List <span className="text-slate-400 font-normal">(Optional)</span>
              </label>

              {ingredientsPreview ? (
                <div className="relative rounded-2xl overflow-hidden border-2 border-slate-300">
                  <img
                    src={ingredientsPreview}
                    alt="Ingredients preview"
                    className="w-full h-48 object-cover"
                  />
                  <button
                    onClick={() => {
                      setIngredientsImage(null);
                      setIngredientsPreview(null);
                    }}
                    className="absolute top-2 right-2 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowModeSelector('ingredients')}
                  className="w-full h-48 rounded-2xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center gap-3 hover:border-[#93BD57] hover:bg-[#93BD57]/5 transition-colors"
                >
                  <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <span className="text-slate-500 font-medium block">Tap to add photo</span>
                    <span className="text-slate-400 text-sm">Camera or Gallery</span>
                  </div>
                </button>
              )}
              {/* Hidden file input for gallery option */}
              <input
                id="ingredients-file-input"
                type="file"
                accept="image/*"
                onChange={handleIngredientsImageSelect}
                className="hidden"
              />
            </div>

            {/* Product Info (Optional) */}
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Product Name <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g., Britannia NutriChoice"
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:border-[#93BD57] focus:ring-2 focus:ring-[#93BD57]/20 outline-none font-medium"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Brand <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  placeholder="e.g., Britannia"
                  className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:border-[#93BD57] focus:ring-2 focus:ring-[#93BD57]/20 outline-none font-medium"
                />
              </div>
            </div>

            {/* Submit Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleSubmit}
              disabled={!nutritionImage}
              className={`w-full py-4 rounded-full font-bold uppercase tracking-widest shadow-lg transition-colors ${nutritionImage
                ? 'bg-[#93BD57] text-white'
                : 'bg-slate-300 text-slate-500 cursor-not-allowed'
                }`}
            >
              Submit Contribution
            </motion.button>
          </motion.div>
        </div>
      </div>
    );
  }

  // Submitting Screen
  if (step === 'submitting') {
    return (
      <div className="h-full bg-[#FFFDE1] flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-full border-4 border-[#93BD57] border-t-transparent animate-spin" />
          <h2 className="text-2xl font-black text-slate-900 mb-2 uppercase tracking-tighter">
            Processing...
          </h2>
          <p className="text-slate-500">
            Our AI is analyzing your photos and calculating the health grade
          </p>
        </motion.div>
      </div>
    );
  }

  // Success Screen
  if (step === 'success' && result) {
    return (
      <div className="h-full bg-[#FFFDE1] flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className="w-24 h-24 mx-auto mb-6 bg-[#93BD57] rounded-full flex items-center justify-center">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h2 className="text-3xl font-black text-slate-900 mb-4 uppercase tracking-tighter">
            Thank You! 🎉
          </h2>

          <p className="text-slate-600 mb-8 font-medium">
            Thanks for contributing! PickBetter will verify the info and update the product into our database. We'll notify you with the score and healthier alternatives once the info is reviewed.
          </p>

          <div className="space-y-3">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={onBack}
              className="w-full py-4 bg-[#93BD57] text-white font-bold uppercase tracking-widest rounded-full shadow-lg"
            >
              Back to Scanner
            </motion.button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Error Screen
  if (step === 'error') {
    return (
      <div className="h-full bg-[#FFFDE1] flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center max-w-md"
        >
          <div className="w-24 h-24 mx-auto mb-6 bg-red-500 rounded-full flex items-center justify-center">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>

          <h2 className="text-2xl font-black text-slate-900 mb-4 uppercase tracking-tighter">
            Oops!
          </h2>

          <p className="text-slate-600 mb-8">
            {error || 'Something went wrong. Please try again.'}
          </p>

          <div className="space-y-3">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setStep('upload')}
              className="w-full py-4 bg-[#93BD57] text-white font-bold uppercase tracking-widest rounded-full shadow-lg"
            >
              Try Again
            </motion.button>

            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={onBack}
              className="w-full py-3 text-slate-500 font-bold uppercase tracking-widest"
            >
              Go Back
            </motion.button>
          </div>
        </motion.div>
      </div>
    );
  }

  return null;
};

export default ContributionScreen;
