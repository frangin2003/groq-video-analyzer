import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import ProgressBar from './ProgressBar';
import SuccessIcon from './SuccessIcon';
import { imageBase64 } from '../imagebase64';

// Mock API calls (unchanged)
const processVideo = async (file, onProgress) => {

  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llava:v1.6',
      prompt: 'Describe the picture with a few sentences',
      images: [imageBase64],
      stream: false
    }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  const data = await response.json();
  console.log('API Response:', data);

  
  console.log('Processing video:', file.name);
  for (let i = 0; i <= 100; i += 10) {
    await new Promise(resolve => setTimeout(resolve, 500));
    onProgress(i);
  }
  return { success: true };
};

const handleExtractFrames = async () => {
  if (!window.electronAPI) {
    console.error('electronAPI is not available');
    return;
  }
  const videoPath = 'c:/Users/charles/Videos/chatgpt2.mp4';
  const outputDir = 'c:/Users/charles/Videos/test';
  const frameRate = 1; // Extract 1 frame per second

  try {
    const result = await window.electronAPI.extractFrames(videoPath, outputDir, frameRate);
    if (result.success) {
      console.log('Frames extracted successfully');
      // Handle success (e.g., update UI, process extracted frames)
    } else {
      console.error('Frame extraction failed:', result.error);
      // Handle error
    }
  } catch (error) {
    console.error('Error calling frame extraction:', error);
    // Handle error
  }
};

const AnalyzeModal = ({ isOpen, onClose, videoFile }) => {
    const [analyzeStarted, setAnalyzeStarted] = useState(false);
    const [frameCount, setFrameCount] = useState(0);
    const [eachXFrame, setEachXFrame] = useState(30);
    const [stepCount, setStepCount] = useState(0);
    const [analyzeProgress, setAnalyzeProgress] = useState(0);
    const [analyzeComplete, setAnalyzeComplete] = useState(false);

    useEffect(() => {
      const processVideoFile = async () => {
        setAnalyzeProgress(0);
        setAnalyzeComplete(false);

        handleExtractFrames();

        try {
          await processVideo(videoFile, (progress) => {
            setAnalyzeProgress(progress);
          });
          setAnalyzeComplete(true);
        } catch (error) {
          console.error('Error processing video:', error);
          alert('Error processing video. Please try again.');
        }
      };

      if (videoFile) {
        processVideoFile();
      }
    }, [videoFile]);

    useEffect(() => {
      if (analyzeComplete) {
        const timer = setTimeout(() => onClose(), 2000);
        return () => clearTimeout(timer);
      }
    }, [analyzeComplete]);

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex justify-center items-center z-50">
        <div className="bg-gray-900 p-6 rounded-xl shadow-2xl relative max-w-md w-full">
          <button onClick={onClose} className="absolute top-2 right-2 text-gray-400 hover:text-white">
            <X size={24} />
          </button>
          <h2 className="text-2xl font-bold mb-4 text-center text-purple-400">
          {analyzeComplete ? 'Processing Complete!' : `Processing ${videoFile?.name}`}
        </h2>
        {!analyzeComplete ? (
          <div className="mb-4">
            <ProgressBar progress={analyzeProgress} />
            <p className="text-center mt-2">{analyzeProgress}% Complete</p>
          </div>
        ) : (
          <div className="text-center">
            <SuccessIcon />
            <p className="mt-4 text-green-400">Your video has been successfully processed!</p>
          </div>
        )}
        </div>
      </div>
    );
  };

export default AnalyzeModal;