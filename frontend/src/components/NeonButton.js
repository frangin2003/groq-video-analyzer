const NeonButton = ({ children, className = '', onClick, hidden = false }) => {
  if (hidden) return null;
  
  return (
    <button
      onClick={onClick}
      className={`
        bg-gradient-to-r from-purple-600 to-pink-600
        hover:from-purple-500 hover:to-pink-500
        text-white font-semibold
        rounded-lg shadow-lg
        transform transition-all duration-300
        hover:scale-105 hover:shadow-xl
        focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50
        ${className}
      `}
    >
      {children}
    </button>
  );
};

export default NeonButton;
