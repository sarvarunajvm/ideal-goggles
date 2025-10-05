import { useBatchSelectionStore } from '../../stores/batchSelectionStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  Trash2,
  Tag,
  X,
  CheckSquare,
  Square,
} from 'lucide-react';
import { useState } from 'react';
import { BatchExportDialog } from './BatchExportDialog';
import { BatchDeleteDialog } from './BatchDeleteDialog';
import { BatchTagDialog } from './BatchTagDialog';

interface BatchActionsProps {
  totalItems: number;
  onSelectAll?: () => void;
}

export function BatchActions({ totalItems, onSelectAll }: BatchActionsProps) {
  const {
    selectionMode,
    selectedIds,
    getSelectedCount,
    toggleSelectionMode,
    clearSelection,
  } = useBatchSelectionStore();

  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [tagDialogOpen, setTagDialogOpen] = useState(false);

  const selectedCount = getSelectedCount();

  if (!selectionMode) {
    return (
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center gap-2">
          <CheckSquare className="h-5 w-5 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {totalItems} photos
          </span>
        </div>
        <Button
          size="sm"
          onClick={toggleSelectionMode}
          className="flex items-center gap-2 !bg-gradient-to-r !from-[rgb(var(--purple-rgb))] !to-[rgb(var(--purple-rgb))] hover:!from-[rgb(var(--purple-rgb))]/80 hover:!to-[rgb(var(--purple-rgb))]/80 !text-white !border-[rgb(var(--purple-rgb))]/50 !shadow-[var(--shadow-purple)] hover:!shadow-[var(--shadow-purple)] hover:scale-105 !font-semibold transition-all"
        >
          <Square className="h-4 w-4" />
          Select
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between p-4 border-b bg-card shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-sm">
              {selectedCount} selected
            </Badge>
          </div>

          {selectedCount > 0 && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => setExportDialogOpen(true)}
                className="flex items-center gap-2 !bg-gradient-to-r !from-[rgb(var(--cyan-rgb))] !to-[rgb(var(--cyan-rgb))] hover:!from-[rgb(var(--cyan-rgb))]/80 hover:!to-[rgb(var(--cyan-rgb))]/80 !text-black !border-[rgb(var(--cyan-rgb))]/50 !shadow-[var(--shadow-cyan)] hover:!shadow-[var(--shadow-cyan)] hover:scale-105 !font-semibold transition-all"
              >
                <Download className="h-4 w-4" />
                Export
              </Button>

              <Button
                size="sm"
                onClick={() => setTagDialogOpen(true)}
                className="flex items-center gap-2 !bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all"
              >
                <Tag className="h-4 w-4" />
                Tag
              </Button>

              <Button
                size="sm"
                onClick={() => setDeleteDialogOpen(true)}
                className="flex items-center gap-2 !bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onSelectAll && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onSelectAll}
              className="flex items-center gap-2 !text-[var(--neon-green)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--green-rgb))]/20 hover:!to-[rgb(var(--green-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-green)] !transition-all"
            >
              <CheckSquare className="h-4 w-4" />
              Select All
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={clearSelection}
            disabled={selectedCount === 0}
            className="flex items-center gap-2 !text-[var(--neon-cyan)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--cyan-rgb))]/20 hover:!to-[rgb(var(--cyan-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-cyan)] !transition-all disabled:opacity-50"
          >
            Clear
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSelectionMode}
            className="flex items-center gap-2 !text-[var(--neon-red)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--red-rgb))]/20 hover:!to-[rgb(var(--red-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-red)] !transition-all"
          >
            <X className="h-4 w-4" />
            Cancel
          </Button>
        </div>
      </div>

      {/* Batch operation dialogs */}
      <BatchExportDialog
        open={exportDialogOpen}
        onOpenChange={setExportDialogOpen}
        selectedIds={Array.from(selectedIds)}
      />
      <BatchDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        selectedIds={Array.from(selectedIds)}
      />
      <BatchTagDialog
        open={tagDialogOpen}
        onOpenChange={setTagDialogOpen}
        selectedIds={Array.from(selectedIds)}
      />
    </>
  );
}
