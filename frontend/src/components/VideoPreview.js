import { Play } from 'lucide-react';

const VideoPreview = ({ result, isCompact, onPlay }) => {
    // Get the frame path from the first frame in the sequence
    const framePath = result.frame_paths[0];
    
    return (
      <div className="relative cursor-pointer" onClick={() => onPlay(result)}>
        <img
          src={`http://localhost:8000/${framePath}`}
          alt="Frame"
          className={`object-cover rounded-lg shadow-md ${isCompact ? 'w-full h-24' : 'w-full h-48'}`}
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 hover:opacity-100 transition-opacity duration-300">
          <Play className="text-white" size={isCompact ? 24 : 48} />
        </div>
      </div>
    );
  };

export default VideoPreview;
