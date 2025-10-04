import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, AlertTriangle, Trash2 } from 'lucide-react';
import axios from 'axios';
import { useBatchSelectionStore } from '../../stores/batchSelectionStore';

const API_BASE = 'http://localhost:5555';

interface BatchDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedIds: string[];
}

export function BatchDeleteDialog({
  open,
  onOpenChange,
  selectedIds,
}: BatchDeleteDialogProps) {
  const { toast } = useToast();
  const { clearSelection, disableSelectionMode } = useBatchSelectionStore();
  const [permanent, setPermanent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/api/batch/delete`, {
        photo_ids: selectedIds,
        permanent,
      });

      const jobId = response.data.job_id;

      toast({
        title: permanent ? 'Permanent Delete Started' : 'Move to Trash Started',
        description: `Processing ${selectedIds.length} photos. Job ID: ${jobId}`,
      });

      clearSelection();
      disableSelectionMode();
      onOpenChange(false);
      setPermanent(false);
    } catch (error) {
      toast({
        title: 'Delete Failed',
        description: error instanceof Error ? error.message : 'Failed to start delete operation',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Delete Photos
          </DialogTitle>
          <DialogDescription>
            {permanent
              ? `Permanently delete ${selectedIds.length} selected photos. This action cannot be undone.`
              : `Move ${selectedIds.length} selected photos to trash. You can restore them from your system trash.`}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="permanent"
              checked={permanent}
              onCheckedChange={(checked) => setPermanent(checked as boolean)}
            />
            <Label
              htmlFor="permanent"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Permanently delete (cannot be recovered)
            </Label>
          </div>

          {permanent && (
            <div className="mt-4 p-3 rounded-md bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive font-medium">
                ⚠️ Warning: This will permanently delete the files from your disk.
                This action cannot be undone!
              </p>
            </div>
          )}

          {!permanent && (
            <div className="mt-4 p-3 rounded-md border dark:bg-primary/10 dark:border-primary/30 bg-primary/10 border-primary/30">
              <p className="text-sm text-primary dark:text-primary/90">
                Photos will be moved to your system trash and can be restored if needed.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              setPermanent(false);
            }}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                {permanent ? 'Delete Permanently' : 'Move to Trash'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
