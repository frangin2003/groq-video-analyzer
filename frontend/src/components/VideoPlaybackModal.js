import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';

const VideoPlaybackModal = ({ isOpen, onClose, video }) => {
    const videoRef = useRef(null);
    
    useEffect(() => {
        const videoElement = videoRef.current;
        if (videoElement && video) {
            // Set initial time when video is loaded
            const handleLoadedMetadata = () => {
                videoElement.currentTime = video.time_start;
            };

            // Check if playback has reached the end time
            const handleTimeUpdate = () => {
                if (videoElement.currentTime >= video.time_end) {
                    videoElement.pause();
                    videoElement.currentTime = video.time_end;
                }
            };

            videoElement.addEventListener('loadedmetadata', handleLoadedMetadata);
            videoElement.addEventListener('timeupdate', handleTimeUpdate);

            return () => {
                videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
                videoElement.removeEventListener('timeupdate', handleTimeUpdate);
            };
        }
    }, [video]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
            <div className="bg-gray-900 p-4 rounded-xl shadow-2xl relative max-w-4xl w-full">
                <button onClick={onClose} className="absolute top-2 right-2 text-gray-400 hover:text-white">
                    <X size={24} />
                </button>
                <h2 className="text-xl font-bold mb-4 text-purple-300"></h2>
                <video
                    ref={videoRef}
                    src={`videos/${video.video_path.replace(/\\/g, '').replace(/\//g, '').replace('videos', '')}`}
                    className="w-full rounded-lg"
                    controls
                    autoPlay
                />
            </div>
        </div>
    );
};

export default VideoPlaybackModal;
