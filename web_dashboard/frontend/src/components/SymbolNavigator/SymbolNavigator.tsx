import React from 'react';

interface SymbolNavigatorProps {
  onSymbolClick?: (symbol: any) => void;
}

export const SymbolNavigator: React.FC<SymbolNavigatorProps> = ({ onSymbolClick }) => {
  return (
    <div className="p-4 text-gray-500">
      Symbol Navigator - Coming Soon
    </div>
  );
};

