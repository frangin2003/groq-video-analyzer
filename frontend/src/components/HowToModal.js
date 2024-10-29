import { X } from 'lucide-react';

const HowToModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
        <div className="bg-gray-900 p-6 rounded-xl shadow-2xl relative max-w-4xl w-full">
          <button onClick={onClose} className="absolute top-2 right-2 text-gray-400 hover:text-white">
            <X size={24} />
          </button>
          <ul className="list-disc list-inside mb-8 text-white space-y-2">
            <li>📂 Analyze videos to extract frames, describe them with AI, and store embeddings in a vector database.</li>
            <li>🔍 Perform natural language searches to find specific sequences across all indexed videos.</li>
            <li>🎬 Extract and utilize video sequences based on your search results.</li>
          </ul>
          <p className="text-gray-300">
            This app allows you to analyze video files, automatically extracting frames eery 2 seconds, describing them using generative AI, and storing them as embeddings in a local vector database. You can then perform natural language searches to find specific sequences across all indexed videos. A sequence is a subset of a video, and a video can contain none or many sequences corresponding to the search.
          </p>
        </div>
      </div>
    );
  };

export default HowToModal;