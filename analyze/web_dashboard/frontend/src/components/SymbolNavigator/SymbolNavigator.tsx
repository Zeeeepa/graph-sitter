import React from 'react';

interface Symbol {
  id: string;
  name: string;
  type: 'function' | 'class' | 'variable' | 'interface' | 'type';
  location: {
    file: string;
    line: number;
    column: number;
  };
  scope?: string;
}

interface SymbolNavigatorProps {
  onSymbolClick?: (symbol: Symbol) => void;
  symbols?: Symbol[];
}

export const SymbolNavigator: React.FC<SymbolNavigatorProps> = ({ onSymbolClick, symbols = [] }) => {
  const handleSymbolClick = (symbol: Symbol) => {
    if (onSymbolClick) {
      onSymbolClick(symbol);
    }
  };

  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Symbols</h3>
      {symbols.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-sm">
          No symbols found. Select a file to view its symbols.
        </div>
      ) : (
        <div className="space-y-1">
          {symbols.map((symbol) => (
            <button
              key={symbol.id}
              onClick={() => handleSymbolClick(symbol)}
              className="w-full text-left px-2 py-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex items-center space-x-2"
            >
              <span className="text-blue-600 dark:text-blue-400 font-mono text-xs">
                {symbol.type.charAt(0).toUpperCase()}
              </span>
              <span className="text-gray-800 dark:text-gray-200">{symbol.name}</span>
              <span className="text-gray-500 dark:text-gray-400 text-xs ml-auto">
                {symbol.location.line}:{symbol.location.column}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
