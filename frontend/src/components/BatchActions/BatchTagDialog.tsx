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
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, X, Plus } from 'lucide-react';
import axios from 'axios';
import { useBatchSelectionStore } from '../../stores/batchSelectionStore';

const API_BASE = 'http://localhost:5555';

interface BatchTagDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedIds: string[];
}

export function BatchTagDialog({
  open,
  onOpenChange,
  selectedIds,
}: BatchTagDialogProps) {
  const { toast } = useToast();
  const { clearSelection } = useBatchSelectionStore();
  const [operation, setOperation] = useState<'add' | 'remove' | 'replace'>('add');
  const [tags, setTags] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAddTag = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !tags.includes(trimmedValue)) {
      setTags([...tags, trimmedValue]);
      setInputValue('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleTag = async () => {
    if (tags.length === 0) {
      toast({
        title: 'Error',
        description: 'Please add at least one tag',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/api/batch/tag`, {
        photo_ids: selectedIds,
        tags,
        operation,
      });

      const jobId = response.data.job_id;

      toast({
        title: 'Tagging Started',
        description: `Processing ${selectedIds.length} photos. Job ID: ${jobId}`,
      });

      clearSelection();
      onOpenChange(false);
      setTags([]);
      setInputValue('');
      setOperation('add');
    } catch (error) {
      toast({
        title: 'Tagging Failed',
        description: error instanceof Error ? error.message : 'Failed to start tagging operation',
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
          <DialogTitle>Tag Photos</DialogTitle>
          <DialogDescription>
            {operation === 'add' && `Add tags to ${selectedIds.length} selected photos`}
            {operation === 'remove' && `Remove tags from ${selectedIds.length} selected photos`}
            {operation === 'replace' && `Replace all tags on ${selectedIds.length} selected photos`}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Operation type */}
          <div className="space-y-2">
            <Label htmlFor="operation">Operation</Label>
            <Select value={operation} onValueChange={(v) => setOperation(v as any)}>
              <SelectTrigger id="operation">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="add">Add tags (keep existing)</SelectItem>
                <SelectItem value="remove">Remove tags</SelectItem>
                <SelectItem value="replace">Replace all tags</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tag input */}
          <div className="space-y-2">
            <Label htmlFor="tagInput">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tagInput"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter a tag and press Enter"
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddTag}
                disabled={!inputValue.trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Tag list */}
          {tags.length > 0 && (
            <div className="space-y-2">
              <Label>Selected Tags ({tags.length})</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[60px]">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 hover:bg-destructive/20 rounded-full p-0.5"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              setTags([]);
              setInputValue('');
              setOperation('add');
            }}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button onClick={handleTag} disabled={loading || tags.length === 0}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              'Apply Tags'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
