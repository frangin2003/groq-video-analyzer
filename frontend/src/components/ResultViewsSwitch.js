import { LayoutGrid, LayoutList} from 'lucide-react';

const ResultViewsSwitch = ({ isCompact, setIsCompact }) => (
    <div className="flex items-center justify-center mb-6">
      <button
        className={`p-2 rounded-l-lg ${isCompact ? 'bg-purple-600' : 'bg-gray-700'}`}
        onClick={() => setIsCompact(true)}
      >
        <LayoutList size={24} />
      </button>
      <button
        className={`p-2 rounded-r-lg ${!isCompact ? 'bg-purple-600' : 'bg-gray-700'}`}
        onClick={() => setIsCompact(false)}
      >
        <LayoutGrid size={24} />
      </button>
    </div>
  );

export default ResultViewsSwitch;