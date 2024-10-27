import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import ProgressBar from './ProgressBar';
import SuccessIcon from './SuccessIcon';

const AnalyzeModal = ({ isOpen, onClose, videoFile }) => {
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analyzeComplete, setAnalyzeComplete] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const processVideoFile = async () => {
      if (!videoFile) return;

      setAnalyzeProgress(0);
      setAnalyzeComplete(false);
      setError(null);

      const formData = new FormData();
      formData.append('file', videoFile);

      try {
        // Get the auth token from localStorage
        const token = localStorage.getItem('auth_token');
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,  // Add the auth token
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const { task_id } = await response.json();

        // Also add auth token to WebSocket connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/${task_id}?token=${token}`;

        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.progress !== undefined) {
            setAnalyzeProgress(data.progress);
            if (data.progress === 100) {
              setAnalyzeComplete(true);
              ws.close();
            }
          }
          if (data.error) {
            setError(data.error);
            ws.close();
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setError('WebSocket connection failed');
        };

        return () => {
          ws.close();
        };
      } catch (error) {
        console.error('Error processing video:', error);
        setError('Error processing video. Please try again.');
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
  }, [analyzeComplete, onClose]);

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
        {error ? (
          <div className="text-center text-red-500 mb-4">{error}</div>
        ) : !analyzeComplete ? (
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
