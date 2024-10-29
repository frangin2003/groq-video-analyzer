import React, { useState, useEffect, useCallback } from 'react';
import { Search, Upload, Video, Clock, Film } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import VideoPreview from './components/VideoPreview';
import AnalyzeModal from './components/AnalyzeModal';
import VideoPlaybackModal from './components/VideoPlaybackModal';
import ResultViewsSwitch from './components/ResultViewsSwitch';
import HowToModal from './components/HowToModal';
import NeonButton from './components/NeonButton';
import { getAuthHeaders } from './utils/auth';

const searchVideoSequences = async (query) => {
  try {
    console.log("🟡 Making API call to search sequences...");
    const response = await fetch(`/api/search_video_sequences/${encodeURIComponent(query)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    console.log("🟡 Got response from API");
    const data = await response.json();
    console.log("🟡 Parsed response data:", data);
    
    return data.results || [];

  } catch (error) {
    console.error("🔴 Error in searchVideoSequences:", error);
    return [];
  }
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
  const isLocal = process.env.REACT_APP_LOCAL === 'true';
  const [videoFile, setVideoFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzeModalOpen, setIsAnalyzeModalOpen] = useState(false);
  const [isCompact, setIsCompact] = useState(true);
  const [playbackVideo, setPlaybackVideo] = useState(null);
  const [isHowToModalOpen, setIsHowToModalOpen] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(isLocal);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleVideoUpload = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      setVideoFile(file);
      setIsAnalyzeModalOpen(true);
    }
  }, []);  // Empty dependencies since it only uses setState functions

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      handleVideoUpload({ target: { files: [file] } });
    }
  }, [handleVideoUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: 'video/*',
    multiple: false
  });

  useEffect(() => {
    // Check if there's an existing auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/auth?password=${encodeURIComponent(password)}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('auth_token', 'authenticated');
        setError('');
      } else {
        setError('Invalid password');
      }
    } catch (error) {
      console.error('Auth error:', error);
      setError('Error authenticating. Please try again.');
    }
  };

  // Move the style useEffect here, before any conditional returns
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

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-black">
        <div className="max-w-md w-full space-y-8 p-8 bg-gray-800 rounded-xl shadow-2xl">
          <div>
            <h1 className="text-4xl font-bold text-center neon-title mb-2">
              SequenceFinder
            </h1>
            <h2 className="text-xl text-center text-purple-300">
              Enter password to continue
            </h2>
          </div>
          <form onSubmit={handleLogin} className="mt-8 space-y-6">
            <div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-700 bg-gray-900 placeholder-gray-400 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter password"
              />
            </div>
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Sign in
            </button>
          </form>
        </div>
      </div>
    );
  }

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

  const handleExtract = async (sequence) => {
    try {
        // Create query parameters
        const params = new URLSearchParams({
            video_path: sequence.video_path,
            time_start: sequence.time_start,
            time_end: sequence.time_end
        });

        const response = await fetch(
            `/api/extract_sequence?${params.toString()}`,
            {
                method: 'GET',
                headers: getAuthHeaders(),
            }
        );

        if (!response.ok) {
            console.error('Extract failed:', await response.text());
            throw new Error('Extract failed');
        }

        // Get the blob from the response
        const blob = await response.blob();
        
        // Create a download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sequence_${sequence.frame_start}-${sequence.frame_end}.mp4`;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error extracting sequence:', error);
        alert('Failed to extract sequence. Please try again.');
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-900 to-black text-white font-sans overflow-hidden">
      <header className="p-4 sm:p-8">
        <div className="flex justify-between items-center mb-8 sm:mb-12">
          <div className="flex flex-col items-start">
            <h1 className="text-4xl sm:text-5xl font-bold neon-title mr-2.5">
              SequenceFinder
            </h1>
            {!process.env.REACT_APP_LOCAL && (
              <a href="https://groq.com" target="_blank" rel="noopener noreferrer" className="mt-2">
                <img
                  src="https://groq.com/wp-content/uploads/2024/03/PBG-mark1-color.svg"
                  alt="Powered by Groq for fast inference."
                  className="h-12"
                />
              </a>
            )}
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

        <div id="upload-search" className="flex flex-col space-y-4">
          <div className="flex flex-col sm:flex-row justify-center mb-4 sm:mb-8 space-y-4 sm:space-y-0 sm:space-x-4">
            {/* Drag & drop area */}
            <div
              {...getRootProps()}
              className={`
                flex items-center justify-center p-6 border-2 border-dashed rounded-lg cursor-pointer
                transition-all duration-300 bg-gray-800 bg-opacity-50
                ${isDragActive ? 'border-pink-500 bg-opacity-70' : 'border-purple-500'}
                hover:border-pink-500 hover:bg-opacity-70
                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50
                w-[300px]
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

            {/* Search input and quick links container */}
            <div className="flex-grow flex flex-col space-y-2 max-w-xl"> {/* Added max-w-xl to limit width */}
              {/* Search input */}
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
              
              {/* Quick action links */}
              <div className="flex justify-center space-x-8">
                <button
                  onClick={() => {
                    setSearchResults([{
                      id: 'paris',
                      hideExtract: true,
                      video_path: '0f6fda2a-5cb0-445b-855e-7ff68f209785_paris_short.mp4',
                      frame_start: 0,
                      frame_end: 10,
                      time_start: 0,
                      time_end: 20,
                      duration: 20,
                      description: 'A drone shot of Paris. https://commons.wikimedia.org/wiki/File:33_minutes_Paris,_France,_drone.webm',
                      frame_paths: ['frames/0f6fda2a-5cb0-445b-855e-7ff68f209785_frame_4.jpg']
                    }, {
                      id: 'cycling_denmark',
                      hideExtract: true,
                      video_path: '6bee1558-4097-4463-acdd-c3dcbc2c71cc_Dänemark_Teil_2_002.mp4',
                      frame_start: 0,
                      frame_end: 101,
                      time_start: 0,
                      time_end: 199,
                      duration: 199,
                      description: 'A cycling trip in Denmark (short). From SaftRAD Youtube channel. https://commons.wikimedia.org/wiki/File:D%C3%A4nemark_Teil_2_-_mit_dem_E-Bike_nach_Kopenhagen_-_Puttgarden_-_Faxe.webm',
                      frame_paths: ['frames/6bee1558-4097-4463-acdd-c3dcbc2c71cc_frame_69.jpg']
                    }, {
                      id: 'steamboat_willie',
                      hideExtract: true,
                      video_path: 'e39d936f-5041-46b8-954a-beece034abf4_steamboat willie 001.mp4',
                      frame_start: 0,
                      frame_end: 69,
                      time_start: 0,
                      time_end: 136,
                      duration: 136,
                      description: 'The classic steamboat Willie (shortened). https://commons.wikimedia.org/wiki/File:Steamboat_Willie_(1928)_by_Walt_Disney.webm',
                      frame_paths: ['frames/e39d936f-5041-46b8-954a-beece034abf4_frame_17.jpg']
                    }]);
                  }}
                  className="text-purple-300 hover:text-pink-500 transition-colors duration-300 underline"
                >
                  List out all indexed videos
                </button>
                <a
                  href="/video_sample_to_test/Paris_by_night.mp4"
                  download
                  className="text-purple-300 hover:text-pink-500 transition-colors duration-300 underline"
                >
                  Download sample to test
                </a>
              </div>
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
            {searchResults.map((sequence) => (
              <div key={sequence.id} className={`bg-gray-800 bg-opacity-50 p-4 sm:p-6 rounded-xl shadow-lg hover:bg-gray-800 transform transition-all duration-300 ${isCompact ? 'flex items-start gap-4' : 'hover:scale-105'}`}>
                <div className={`${isCompact ? 'w-[300px] flex-shrink-0' : ''}`}>
                  <VideoPreview result={sequence} isCompact={isCompact} onPlay={handlePlayVideo} />
                </div>
                <div className={isCompact ? 'flex-grow' : 'mt-4'}>
                  <p className={`text-purple-300 ${isCompact ? 'text-sm mb-2' : 'text-lg mb-4'} line-clamp-2`}>
                    {sequence.description.length > 250 
                      ? `${sequence.description.substring(0, 250)}...` 
                      : sequence.description}
                  </p>
                  
                  {/* Metadata information */}
                  <div className={`grid gap-2 mb-4 ${isCompact ? 'text-xs grid-cols-8' : 'text-sm grid-cols-3'}`}>
                    <div className="flex items-center">
                      <Film size={isCompact ? 14 : 16} className="mr-1 text-pink-400" />
                      <span className="text-gray-300">Frames: </span>
                      <span className="ml-1 font-semibold whitespace-nowrap">
                        {sequence.frame_start}-{sequence.frame_end}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <Clock size={isCompact ? 14 : 16} className="mr-1 text-green-400" />
                      <span className="text-gray-300">Time: </span>
                      <span className="ml-1 font-semibold">
                        {sequence.time_start.toFixed(2)}s - {sequence.time_end.toFixed(2)}s
                      </span>
                    </div>
                    <div className="flex items-center">
                      <Clock size={isCompact ? 14 : 16} className="mr-1 text-green-400" />
                      <span className="text-gray-300">Duration: </span>
                      <span className="ml-1 font-semibold">
                        {sequence.duration.toFixed(2)}s
                      </span>
                    </div>
                    <div className={`flex items-center ${isCompact ? 'col-span-2' : ''}`}>
                      <Video size={isCompact ? 14 : 16} className="mr-1 text-purple-400" />
                      <span className="text-gray-300">Video: </span>
                      <span className="ml-1 font-semibold whitespace-nowrap">
                        {sequence.video_path.split('\\').pop()}
                      </span>
                    </div>
                  </div>

                  <NeonButton 
                    className={`flex items-center justify-center ${isCompact ? 'text-sm py-1 px-2' : 'w-full'}`}
                    onClick={() => handleExtract(sequence)}
                    hidden={sequence.hideExtract} // Add this line
                  >
                    <Video className="mr-2" size={isCompact ? 16 : 20} />
                    Extract Sequence
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
        /* Add this new style for text truncation */
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default App;
