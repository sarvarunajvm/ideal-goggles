import { useState } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { FolderPlus, X, Folder } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function FolderSelectionStep() {
  const {
    selectedFolders,
    addFolder,
    removeFolder,
    nextStep,
    prevStep,
  } = useOnboardingStore();
  const [isSelecting, setIsSelecting] = useState(false);
  const [manualPath, setManualPath] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);

  const handleSelectFolder = async () => {
    setIsSelecting(true);
    try {
      // Check if we're in Electron environment
      if (window.electronAPI?.selectDirectory) {
        // Use Electron IPC to open native folder picker
        const result = await window.electronAPI.selectDirectory();
        if (result && !result.canceled && result.filePaths.length > 0) {
          const folderPath = result.filePaths[0];
          if (!selectedFolders.includes(folderPath)) {
            addFolder(folderPath);
          }
        }
      } else {
        // Fallback for web/development - show input field instead of prompt
        setShowManualInput(true);
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
      // Show manual input as fallback
      setShowManualInput(true);
    } finally {
      setIsSelecting(false);
    }
  };

  const handleManualAdd = () => {
    if (manualPath && !selectedFolders.includes(manualPath)) {
      addFolder(manualPath);
      setManualPath('');
      setShowManualInput(false);
    }
  };

  const handleNext = () => {
    if (selectedFolders.length > 0) {
      nextStep();
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground">
          Where Are Your Photos?
        </h2>
        <p className="mt-2 text-muted-foreground">
          Choose the folders where you keep your photos
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Default: your Pictures folder ({navigator.platform.includes('Win') ? '%USERPROFILE%\\Pictures' : '~/Pictures'})
        </p>
      </div>

      {/* Folder list */}
      <div className="min-h-[200px] space-y-2">
        {selectedFolders.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border/50 p-12 text-muted-foreground">
            <Folder className="h-12 w-12 mb-4" />
            <p className="text-center">
              No folders selected yet.
              <br />
              Click "Add Folder" to get started.
            </p>
          </div>
        ) : (
          selectedFolders.map((folder) => (
            <div
              key={folder}
              className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-3"
            >
              <div className="flex items-center space-x-3">
                <Folder className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium text-foreground">
                  {folder}
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeFolder(folder)}
                className="h-8 w-8 p-0 !text-[var(--neon-red)] hover:!bg-gradient-to-r hover:!from-[rgb(var(--red-rgb))]/20 hover:!to-[rgb(var(--red-rgb))]/30 hover:!shadow-md hover:!shadow-[var(--shadow-red)] !transition-all"
                aria-label="Remove folder"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))
        )}
      </div>

      {/* Manual input field for web/development */}
      {showManualInput && (
        <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
          <p className="text-sm text-muted-foreground">Enter folder path manually:</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={manualPath}
              onChange={(e) => setManualPath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleManualAdd();
                }
              }}
              placeholder="/path/to/your/photos"
              className="flex-1 px-3 py-2 text-sm rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <Button
              onClick={handleManualAdd}
              disabled={!manualPath}
              size="sm"
              className="!bg-gradient-to-r !from-[rgb(var(--green-rgb))] !to-[rgb(var(--green-rgb))] hover:!from-[rgb(var(--green-rgb))]/80 hover:!to-[rgb(var(--green-rgb))]/80 !text-black !border-[rgb(var(--green-rgb))]/50 !shadow-[var(--shadow-green)] hover:!shadow-[var(--shadow-green)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
            >
              Add
            </Button>
            <Button
              onClick={() => {
                setShowManualInput(false);
                setManualPath('');
              }}
              size="sm"
              className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Add folder button */}
      {!showManualInput && (
        <Button
          onClick={handleSelectFolder}
          disabled={isSelecting}
          className="w-full !bg-gradient-to-r !from-[rgb(var(--pink-rgb))] !to-[rgb(var(--pink-rgb))] hover:!from-[rgb(var(--pink-rgb))]/80 hover:!to-[rgb(var(--pink-rgb))]/80 !text-black !border-[rgb(var(--pink-rgb))]/50 !shadow-[var(--shadow-pink)] hover:!shadow-[var(--shadow-pink)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
        >
          <FolderPlus className="h-5 w-5 mr-2" />
          <span>
            {isSelecting ? 'Selecting...' : 'Add Folder'}
          </span>
        </Button>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <Button
          onClick={prevStep}
          className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 !font-semibold transition-all"
        >
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={selectedFolders.length === 0}
          className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
