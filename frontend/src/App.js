import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Search, Upload, Video, Clock, Film } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import VideoPreview from './components/VideoPreview';
import AnalyzeModal from './components/AnalyzeModal';
import VideoPlaybackModal from './components/VideoPlaybackModal';
import ResultViewsSwitch from './components/ResultViewsSwitch';
import HowToModal from './components/HowToModal';
import NeonButton from './components/NeonButton';
import { imageBase64 } from './imagebase64';

const searchVideoSequences = async (query) => {
  console.log('Searching for:', query);
  await new Promise(resolve => setTimeout(resolve, 500));
  return [
    { id: 1, imageBase64: imageBase64, frameStart: 255, frameEnd: 300, timeStartMs: 1001, timeEndMs: 2001, durationMs: 1000, videoUrl: 'https://example.com/video1.mp4', description: 'A person walking in a neon-lit street, surrounded by the vibrant glow of neon signs and the bustling atmosphere of a futuristic city. The scene captures the essence of a cyberpunk world, with reflections of neon lights on wet pavement and the distant hum of technology in the background. The person\'s silhouette is highlighted by the colorful lights, creating a striking contrast against the dark surroundings. This sequence offers a glimpse into a world where technology and urban life are intertwined, creating a visually stunning and immersive experience.' },
    { id: 2, imageBase64: imageBase64, frameStart: 300, frameEnd: 350, timeStartMs: 2002, timeEndMs: 3000, durationMs: 998, videoUrl: 'https://example.com/video1.mp4', description: 'A futuristic car zooming through a cyberpunk city, navigating the neon-lit streets with incredible speed and precision. The car\'s sleek design and advanced technology are on full display as it weaves through traffic, leaving a trail of light in its wake. The cityscape is a dazzling array of towering skyscrapers, holographic advertisements, and bustling crowds, all bathed in the glow of neon lights. This sequence captures the thrill and excitement of a high-speed chase in a world where technology reigns supreme, offering a breathtaking view of a future metropolis.' },
    { id: 3, imageBase64: imageBase64, frameStart: 322, frameEnd: 350, timeStartMs: 2520, timeEndMs: 3500, durationMs: 980, videoUrl: 'https://example.com/video1.mp4', description: 'A holographic dog playing in a virtual park, showcasing the seamless integration of augmented reality into everyday life. The dog, rendered in stunning detail, interacts with its environment and other virtual elements, creating a lifelike and engaging experience. The park itself is a blend of natural beauty and digital enhancements, with holographic trees, flowers, and playground equipment. This sequence highlights the potential of augmented reality to transform our surroundings and create new forms of entertainment and interaction, blurring the lines between the real and the virtual.' },
    { id: 4, imageBase64: imageBase64, frameStart: 23, frameEnd: 50, timeStartMs: 3000, timeEndMs: 3500, durationMs: 500, videoUrl: 'https://example.com/video2.mp4', description: 'A neon sign flickering in the rain, casting a moody and atmospheric glow over the scene. The sign, with its vibrant colors and intricate design, stands out against the dark, rainy backdrop. Raindrops create ripples on the ground, reflecting the neon lights and adding to the overall ambiance. This sequence captures the essence of a rainy night in a cyberpunk city, where the interplay of light and shadow creates a visually captivating and immersive experience. The flickering sign adds an element of mystery and intrigue, drawing the viewer\'s attention and setting the tone for the scene.' },
    { id: 5, imageBase64: imageBase64, frameStart: 566, frameEnd: 600, timeStartMs: 3500, timeEndMs: 4000, durationMs: 500, videoUrl: 'https://example.com/video2.mp4', description: 'A drone flying through a futuristic cityscape, capturing breathtaking aerial views of the neon-lit metropolis below. The drone\'s smooth and agile movements allow it to navigate the complex urban environment with ease, providing a unique perspective on the city\'s architecture and layout. Skyscrapers, bridges, and streets are all illuminated by the vibrant glow of neon lights, creating a stunning visual spectacle. This sequence showcases the potential of drone technology to explore and document our surroundings, offering a bird\'s-eye view of a world where technology and urban life are seamlessly integrated.' },
    { id: 6, imageBase64: imageBase64, frameStart: 1024, frameEnd: 1200, timeStartMs: 4000, timeEndMs: 5000, durationMs: 1000, videoUrl: 'https://example.com/video3.mp4', description: 'A holographic concert in a virtual arena, featuring a dazzling display of lights, music, and digital effects. The performers, rendered in stunning detail, interact with the audience and the virtual environment, creating an immersive and unforgettable experience. The arena itself is a marvel of digital design, with holographic screens, dynamic lighting, and interactive elements that respond to the music. This sequence captures the excitement and energy of a live concert, enhanced by the limitless possibilities of virtual reality. It offers a glimpse into the future of entertainment, where technology can create new and innovative ways to experience music and performance.' },
  ];
};

const loadingPhrases = [
  "Scanning the multi-versal sequence archives...",
  "Extracting holo-frames from the datasphere...",
  "Unleashing the AI descriptors on visual fragments...",
  "Embedding sequences in the local quantum matrix...",
  "Probing the vector dimension for matching realities...",
  "Decoding visual narratives from the pixel stream...",
  "Syncing with the collective digital consciousness...",
  "Parsing the chronostream for relevant segments...",
  "Interfacing with the cybernetic image cortex...",
  "Materializing sequence data from the virtual ether..."
];

const LoadingComponent = () => {
  const [currentPhrase, setCurrentPhrase] = useState('');
  const [fadeState, setFadeState] = useState('in');

  useEffect(() => {
    const phrases = [...loadingPhrases].sort(() => Math.random() - 0.5);
    let index = 0;

    const changePhrase = () => {
      setFadeState('out');
      setTimeout(() => {
        setCurrentPhrase(phrases[index]);
        setFadeState('in');
        index = (index + 1) % phrases.length;
      }, 500); // Wait for fade out
    };

    const interval = setInterval(changePhrase, 3000); // Change phrase every 3 seconds
    changePhrase(); // Initial phrase

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-center my-12">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-500 mx-auto"></div>
      <p className={`mt-4 text-xl transition-opacity duration-500 ${fadeState === 'in' ? 'opacity-100' : 'opacity-0'}`}>
        {currentPhrase}
      </p>
    </div>
  );
};

const App = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzeModalOpen, setIsAnalyzeModalOpen] = useState(false);
  const [isCompact, setIsCompact] = useState(false);
  const [playbackVideo, setPlaybackVideo] = useState(null);
  const fileInputRef = useRef(null);
  const [isHowToModalOpen, setIsHowToModalOpen] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);

  const handleVideoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setVideoFile(file);
      setIsAnalyzeModalOpen(true);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleSearch = async () => {
    if (searchQuery.trim() === '') return;
    setIsLoading(true);
    try {
      const results = await searchVideoSequences(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching video sequences:', error);
      alert('Error searching video sequences. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const handlePlayVideo = (video) => {
    setPlaybackVideo(video);
  };

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      handleVideoUpload({ target: { files: [file] } });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: 'video/*',
    multiple: false
  });

  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      .neon-title {
        background: linear-gradient(90deg, #ff00ff, #00ffff, #ff00ff);
        background-size: 200% 200%;
        animation: gradientShift 10s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-900 to-black text-white font-sans overflow-hidden">
      <header className="p-4 sm:p-8">
        <div className="flex justify-between items-center mb-8 sm:mb-12">
          <div className="flex flex-col items-start">
            <h1 className="text-4xl sm:text-5xl font-bold neon-title mr-2.5">
              SequenceFinder
            </h1>
            <a href="https://groq.com" target="_blank" rel="noopener noreferrer" className="mt-2">
              <img
                src="https://groq.com/wp-content/uploads/2024/03/PBG-mark1-color.svg"
                alt="Powered by Groq for fast inference."
                className="h-12"
              />
            </a>
          </div>
          <h2 className="text-xl sm:text-2xl font-semibold text-center flex-grow whitespace-nowrap overflow-hidden text-ellipsis">
            Find and extract video sequences with just your words!
          </h2>
          <button
            onClick={() => setIsHowToModalOpen(true)}
            className="text-purple-300 hover:text-pink-500 transition-colors duration-300 underline flex items-center"
          >
            <span className="mr-1">Learn how to use this app</span>
          </button>
        </div>

        <div id="upload-search" className="flex flex-col sm:flex-row justify-center mb-8 sm:mb-12 space-y-4 sm:space-y-0 sm:space-x-4">
          {/* Drag & drop area */}
          <div
            {...getRootProps()}
            className={`
              flex items-center justify-center p-6 border-2 border-dashed rounded-lg cursor-pointer
              transition-all duration-300 bg-gray-800 bg-opacity-50
              ${isDragActive ? 'border-pink-500 bg-opacity-70' : 'border-purple-500'}
              hover:border-pink-500 hover:bg-opacity-70
              focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50
            `}
          >
            <input {...getInputProps()} />
            <div className="text-center">
              <Upload className="mx-auto mb-2" size={24} />
              <p className="text-lg font-semibold">
                {isDragActive ? 'Drop the video here' : 'Drag & drop a video or click to select'}
              </p>
              <p className="text-sm text-gray-400 mt-1">Supported formats: MP4, AVI, MOV</p>
            </div>
          </div>

          {/* Search input */}
          <div className="relative flex-grow max-w-2xl">
            <div className="flex items-stretch">
              <input
                type="text"
                className={`flex-grow p-3 pr-12 bg-gray-800 rounded-l-lg text-lg border-2 border-r-0 ${
                  isInputFocused ? 'border-pink-500' : 'border-purple-600'
                } focus:outline-none transition-all duration-300`}
                placeholder="Search video sequences..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={() => setIsInputFocused(true)}
                onBlur={() => setIsInputFocused(false)}
              />
              <button
                className={`px-3 bg-gray-800 rounded-r-lg text-purple-400 hover:text-pink-500 transition-colors duration-300 border-2 border-l-0 ${
                  isInputFocused ? 'border-pink-500' : 'border-purple-600'
                } focus:outline-none`}
                onClick={handleSearch}
              >
                <Search size={24} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {searchResults.length > 0 && (
            <ResultViewsSwitch isCompact={isCompact} setIsCompact={setIsCompact} />
          )}


      <main className="flex-grow overflow-y-auto custom-scrollbar">
        {isLoading && <LoadingComponent />}

        <div id="search-results" className="p-4 sm:p-8">
          <div className={`grid gap-8 ${isCompact ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
            {searchResults.map((result) => (
              <div key={result.id} className={`bg-gray-800 bg-opacity-50 p-4 sm:p-6 rounded-xl shadow-lg hover:bg-gray-800 transform transition-all duration-300 ${isCompact ? 'flex items-center' : 'hover:scale-105'}`}>
                <VideoPreview result={result} isCompact={isCompact} onPlay={handlePlayVideo} />
                <div className={isCompact ? 'flex-grow ml-4' : 'mt-4'}>
                  <p className={`text-purple-300 ${isCompact ? 'text-sm mb-2' : 'text-lg mb-4'}`}>{result.description}</p>
                  
                  {/* New section for additional information */}
                  <div className={`grid gap-2 mb-4 ${isCompact ? 'text-xs grid-cols-8' : 'text-sm grid-cols-3'}`}>
                    <div className="flex items-center">
                      <Film size={isCompact ? 14 : 16} className="mr-1 text-pink-400" />
                      <span className="text-gray-300">Frames: </span>
                      <span className="ml-1 font-semibold whitespace-nowrap">{result.frameStart} - {result.frameEnd}</span>
                    </div>
                    <div className="flex items-center">
                      <Clock size={isCompact ? 14 : 16} className="mr-1 text-green-400" />
                      <span className="text-gray-300">Duration: </span>
                      <span className="ml-1 font-semibold">{(result.durationMs / 1000).toFixed(2)}s</span>
                    </div>
                    <div className={`flex items-center ${isCompact ? 'col-span-2' : ''}`}>
                      <Clock size={isCompact ? 14 : 16} className="mr-1 text-purple-400" />
                      <span className="text-gray-300">Time: </span>
                      <span className="ml-1 font-semibold whitespace-nowrap">
                        {(result.timeStartMs / 1000).toFixed(2)}s - {(result.timeEndMs / 1000).toFixed(2)}s
                      </span>
                    </div>
                  </div>

                  <NeonButton className={`flex items-center justify-center ${isCompact ? 'text-sm py-1 px-2' : 'w-full'}`}>
                    <Video className="mr-2" size={isCompact ? 16 : 20} />
                    Extract
                  </NeonButton>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <AnalyzeModal
        isOpen={isAnalyzeModalOpen}
        onClose={() => setIsAnalyzeModalOpen(false) }
        videoFile={videoFile}
      />

      <VideoPlaybackModal
        isOpen={!!playbackVideo}
        onClose={() => setPlaybackVideo(null)}
        video={playbackVideo}
      />

      <HowToModal isOpen={isHowToModalOpen} onClose={() => setIsHowToModalOpen(false)} />

      <style jsx global>{`
        body {
          overflow: hidden;
        }
        .custom-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #8B5CF6 rgba(31, 41, 55, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 12px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(31, 41, 55, 0.5);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #8B5CF6, #EC4899);
          border-radius: 10px;
          border: 3px solid rgba(31, 41, 55, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #9C4FFF, #FF2D92);
        }
      `}</style>
    </div>
  );
};

export default App;