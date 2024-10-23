import { X } from 'lucide-react';

const VideoPlaybackModal = ({ isOpen, onClose, video }) => {
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
        <div className="bg-gray-900 p-4 rounded-xl shadow-2xl relative max-w-4xl w-full">
          <button onClick={onClose} className="absolute top-2 right-2 text-gray-400 hover:text-white">
            <X size={24} />
          </button>
          <h2 className="text-xl font-bold mb-4 text-purple-300"></h2>
          <video
            src={`http://localhost:8000/videos/${video.video_path.split('\\').pop()}`}
            className="w-full rounded-lg"
            controls
            autoPlay
          />
        </div>
      </div>
    );
  };

export default VideoPlaybackModal;
