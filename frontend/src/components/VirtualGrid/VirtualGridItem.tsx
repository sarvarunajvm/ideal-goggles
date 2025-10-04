import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useBatchSelectionStore } from '../../stores/batchSelectionStore';
import { Checkbox } from '@/components/ui/checkbox';

interface VirtualGridItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  itemId?: string;
}

export function VirtualGridItem({ children, onClick, itemId }: VirtualGridItemProps) {
  const [isVisible, setIsVisible] = useState(false);
  const itemRef = useRef<HTMLDivElement>(null);
  const { selectionMode, isSelected, toggleSelection } = useBatchSelectionStore();

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!itemRef.current) return;

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '100px', // Load items 100px before they become visible
        threshold: 0.01,
      }
    );

    observer.observe(itemRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  const handleClick = (e: React.MouseEvent) => {
    if (selectionMode && itemId) {
      e.stopPropagation();
      toggleSelection(itemId);
    } else if (onClick) {
      onClick();
    }
  };

  const selected = itemId ? isSelected(itemId) : false;

  return (
    <motion.div
      ref={itemRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
      transition={{ duration: 0.3 }}
      onClick={handleClick}
      className={`cursor-pointer relative ${selected ? 'ring-2 ring-primary ring-offset-2' : ''}`}
    >
      {selectionMode && itemId && isVisible && (
        <div className="absolute top-2 left-2 z-10">
          <div className="bg-background/90 backdrop-blur-sm rounded-md p-1">
            <Checkbox checked={selected} />
          </div>
        </div>
      )}
      {isVisible ? children : <div className="aspect-square bg-muted animate-pulse" />}
    </motion.div>
  );
}
