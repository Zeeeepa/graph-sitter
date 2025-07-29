import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface ActivityBarTab {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface ActivityBarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  tabs: ActivityBarTab[];
  className?: string;
}

export const ActivityBar: React.FC<ActivityBarProps> = ({
  activeTab,
  onTabChange,
  tabs,
  className
}) => {
  return (
    <div className={clsx(
      'w-12 bg-gray-800 dark:bg-gray-900 border-r border-gray-700 dark:border-gray-600 flex flex-col',
      className
    )}>
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        
        return (
          <motion.button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={clsx(
              'relative w-12 h-12 flex items-center justify-center transition-colors',
              isActive 
                ? 'text-white bg-gray-700 dark:bg-gray-800' 
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700 dark:hover:bg-gray-800'
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title={tab.label}
          >
            <Icon className="w-5 h-5" />
            
            {/* Active indicator */}
            {isActive && (
              <motion.div
                layoutId="activeTab"
                className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500"
                initial={false}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </motion.button>
        );
      })}
    </div>
  );
};
