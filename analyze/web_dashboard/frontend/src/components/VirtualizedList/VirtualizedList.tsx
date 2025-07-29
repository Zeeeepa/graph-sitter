import React, { useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (props: { item: T; index: number; style: React.CSSProperties }) => React.ReactNode;
  className?: string;
  overscanCount?: number;
}

export function VirtualizedList<T>({
  items,
  itemHeight,
  renderItem,
  className,
  overscanCount = 5
}: VirtualizedListProps<T>) {
  const ItemRenderer = useMemo(() => {
    return ({ index, style }: { index: number; style: React.CSSProperties }) => {
      const item = items[index];
      return (
        <div style={style}>
          {renderItem({ item, index, style })}
        </div>
      );
    };
  }, [items, renderItem]);

  return (
    <div className={className} style={{ height: '100%', width: '100%' }}>
      <AutoSizer>
        {({ height, width }) => (
          <List
            height={height}
            width={width}
            itemCount={items.length}
            itemSize={itemHeight}
            overscanCount={overscanCount}
          >
            {ItemRenderer}
          </List>
        )}
      </AutoSizer>
    </div>
  );
}
