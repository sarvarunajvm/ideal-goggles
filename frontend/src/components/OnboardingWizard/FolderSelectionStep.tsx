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
        // Fallback for web/development - use a simple prompt
        const folderPath = prompt('Enter the folder path:');
        if (folderPath && !selectedFolders.includes(folderPath)) {
          addFolder(folderPath);
        }
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
      alert('Failed to select folder. Please try again.');
    } finally {
      setIsSelecting(false);
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

      {/* Add folder button */}
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
