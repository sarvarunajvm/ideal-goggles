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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, FolderOpen } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5555';

interface BatchExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedIds: string[];
}

export function BatchExportDialog({
  open,
  onOpenChange,
  selectedIds,
}: BatchExportDialogProps) {
  const { toast } = useToast();
  const [destination, setDestination] = useState('');
  const [format, setFormat] = useState('original');
  const [maxDimension, setMaxDimension] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSelectDestination = async () => {
    try {
      // @ts-expect-error - Electron IPC will be available at runtime
      const result = await window.electron.selectDirectory();
      if (result && !result.canceled && result.filePaths.length > 0) {
        setDestination(result.filePaths[0]);
      }
    } catch (error) {
      console.error('Failed to select destination:', error);
    }
  };

  const handleExport = async () => {
    if (!destination) {
      toast({
        title: 'Error',
        description: 'Please select a destination folder',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/api/batch/export`, {
        photo_ids: selectedIds,
        destination,
        format,
        max_dimension: maxDimension ? parseInt(maxDimension) : null,
      });

      const jobId = response.data.job_id;

      toast({
        title: 'Export Started',
        description: `Exporting ${selectedIds.length} photos. Job ID: ${jobId}`,
      });

      onOpenChange(false);
      setDestination('');
      setFormat('original');
      setMaxDimension('');
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Failed to start export',
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
          <DialogTitle>Export Photos</DialogTitle>
          <DialogDescription>
            Export {selectedIds.length} selected photos to a folder
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Destination folder */}
          <div className="space-y-2">
            <Label htmlFor="destination">Destination Folder</Label>
            <div className="flex gap-2">
              <Input
                id="destination"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="/path/to/export/folder"
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleSelectDestination}
              >
                <FolderOpen className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Format */}
          <div className="space-y-2">
            <Label htmlFor="format">Export Format</Label>
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger id="format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="original">Original</SelectItem>
                <SelectItem value="jpg">JPEG</SelectItem>
                <SelectItem value="png">PNG</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Max dimension (optional) */}
          <div className="space-y-2">
            <Label htmlFor="maxDimension">
              Max Dimension (optional)
            </Label>
            <Input
              id="maxDimension"
              type="number"
              value={maxDimension}
              onChange={(e) => setMaxDimension(e.target.value)}
              placeholder="e.g., 1920 (pixels)"
            />
            <p className="text-xs text-muted-foreground">
              Images will be resized to fit within this dimension while maintaining aspect ratio
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={loading || !destination}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Exporting...
              </>
            ) : (
              'Export'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
