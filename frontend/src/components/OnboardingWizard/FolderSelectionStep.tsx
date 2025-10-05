import { useState } from 'react';
import { useOnboardingStore } from '../../stores/onboardingStore';
import { FolderPlus, X, Folder } from 'lucide-react';

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
              <button
                onClick={() => removeFolder(folder)}
                className="rounded p-1 text-red-500/70 hover:bg-red-500/10 hover:text-red-500 transition-all"
                aria-label="Remove folder"
              >
                <X className="h-4 w-4" />
              </button>
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
            <button
              onClick={handleManualAdd}
              disabled={!manualPath}
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add
            </button>
            <button
              onClick={() => {
                setShowManualInput(false);
                setManualPath('');
              }}
              className="px-4 py-2 text-sm font-medium rounded-md bg-muted hover:bg-muted/80"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Add folder button */}
      {!showManualInput && (
        <button
          onClick={handleSelectFolder}
          disabled={isSelecting}
          className="flex w-full items-center justify-center space-x-2 rounded-lg py-3 font-semibold [background:var(--gradient-gold)] text-black shadow-md shadow-primary/30 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <FolderPlus className="h-5 w-5" />
          <span>
            {isSelecting ? 'Selecting...' : 'Add Folder'}
          </span>
        </button>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={prevStep}
          className="rounded-lg px-6 py-2 font-medium [background:var(--gradient-red)] text-white shadow-md shadow-red-500/30 hover:shadow-lg hover:shadow-red-500/40 hover:scale-[1.02] transition-all"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          disabled={selectedFolders.length === 0}
          className="rounded-lg px-6 py-2 font-semibold [background:var(--gradient-gold)] text-black disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-primary/30 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02] transition-all"
        >
          Next
        </button>
      </div>
    </div>
  );
}
