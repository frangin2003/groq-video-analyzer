const NeonButton = ({ children, onClick, className = '' }) => (
    <button
      className={`bg-purple-700 hover:bg-purple-600 text-white font-bold py-2 px-4 rounded-lg 
                  shadow-[0_0_15px_rgba(147,51,234,0.5)] hover:shadow-[0_0_25px_rgba(147,51,234,0.8)] 
                  transition-all duration-300 ${className}`}
      onClick={onClick}
    >
      {children}
    </button>
  );

export default NeonButton;