const ProgressBar = ({ progress }) => (
  <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
    <div
      className="bg-gradient-to-r from-blue-500 to-purple-600 h-full transition-all duration-500 ease-out"
      style={{ width: `${progress}%` }}
    ></div>
  </div>
);

export default ProgressBar;