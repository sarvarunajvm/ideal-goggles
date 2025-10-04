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
          variant="outline"
          size="sm"
          onClick={toggleSelectionMode}
          className="flex items-center gap-2"
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
                variant="outline"
                size="sm"
                onClick={() => setExportDialogOpen(true)}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setTagDialogOpen(true)}
                className="flex items-center gap-2"
              >
                <Tag className="h-4 w-4" />
                Tag
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteDialogOpen(true)}
                className="flex items-center gap-2 text-destructive hover:text-destructive"
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
              className="flex items-center gap-2"
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
            className="flex items-center gap-2"
          >
            Clear
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSelectionMode}
            className="flex items-center gap-2"
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
