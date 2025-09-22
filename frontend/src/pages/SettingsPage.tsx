import { useState, useEffect } from 'react';
import { apiService, ConfigResponse, IndexStatus } from '../services/api';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';

export default function SettingsPage() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [indexStats, setIndexStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [rootFolders, setRootFolders] = useState<string[]>([]);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [ocrLanguages, setOcrLanguages] = useState<string[]>([]);
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [configData, statusData, statsData] = await Promise.all([
        apiService.getConfig(),
        apiService.getIndexStatus(),
        apiService.getIndexStats(),
      ]);

      setConfig(configData);
      setIndexStatus(statusData);
      setIndexStats(statsData);

      // Update form state
      setRootFolders(configData.roots);
      setOcrLanguages(configData.ocr_languages);
      setFaceSearchEnabled(configData.face_search_enabled);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      setSaving(true);
      setError(null);

      // Update root folders
      await apiService.updateRoots(rootFolders);

      // Update other config
      await apiService.updateConfig({
        ocr_languages: ocrLanguages,
        face_search_enabled: faceSearchEnabled,
      });

      setSuccess('Configuration saved successfully!');
      setTimeout(() => setSuccess(null), 3000);

      // Reload data
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const addRootFolder = () => {
    if (newFolderPath.trim() && !rootFolders.includes(newFolderPath.trim())) {
      setRootFolders([...rootFolders, newFolderPath.trim()]);
      setNewFolderPath('');
    }
  };

  const removeRootFolder = (index: number) => {
    setRootFolders(rootFolders.filter((_, i) => i !== index));
  };

  const startIndexing = async (full = false) => {
    try {
      await apiService.startIndexing(full);
      setSuccess(`${full ? 'Full' : 'Incremental'} indexing started!`);
      setTimeout(() => setSuccess(null), 3000);
      // Reload status
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start indexing');
    }
  };

  const stopIndexing = async () => {
    try {
      await apiService.stopIndexing();
      setSuccess('Indexing stopped!');
      setTimeout(() => setSuccess(null), 3000);
      // Reload status
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop indexing');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <Navigation />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading settings...</p>
          </div>
        </div>
        <StatusBar />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Navigation />

      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

          {/* Status Messages */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <span className="text-red-600 mr-2">❌</span>
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <span className="text-green-600 mr-2">✅</span>
                <span className="text-green-700">{success}</span>
              </div>
            </div>
          )}

          <div className="space-y-8">
            {/* Root Folders Section */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                📁 Root Folders
              </h2>
              <p className="text-gray-600 mb-4">
                Configure which folders to scan for photos. The system will recursively search these directories.
              </p>

              {/* Current Folders */}
              <div className="space-y-2 mb-4">
                {rootFolders.map((folder, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-mono text-sm">{folder}</span>
                    <button
                      onClick={() => removeRootFolder(index)}
                      className="text-red-600 hover:text-red-800 transition-colors"
                    >
                      🗑️ Remove
                    </button>
                  </div>
                ))}
              </div>

              {/* Add New Folder */}
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newFolderPath}
                  onChange={(e) => setNewFolderPath(e.target.value)}
                  placeholder="/path/to/your/photos"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={addRootFolder}
                  disabled={!newFolderPath.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
                >
                  Add Folder
                </button>
              </div>
            </section>

            {/* Indexing Section */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                ⚡ Indexing
              </h2>

              {/* Current Status */}
              {indexStatus && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      indexStatus.status === 'indexing' ? 'bg-blue-100 text-blue-800' :
                      indexStatus.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {indexStatus.status}
                    </span>
                  </div>

                  {indexStatus.status === 'indexing' && (
                    <div className="space-y-1 text-sm text-gray-600">
                      <div>Phase: {indexStatus.progress.current_phase}</div>
                      {indexStatus.progress.total_files > 0 && (
                        <div>
                          Progress: {indexStatus.progress.processed_files}/{indexStatus.progress.total_files} files
                        </div>
                      )}
                    </div>
                  )}

                  {indexStatus.errors.length > 0 && (
                    <div className="mt-2">
                      <details className="text-sm">
                        <summary className="text-red-600 cursor-pointer">
                          {indexStatus.errors.length} error(s)
                        </summary>
                        <div className="mt-2 space-y-1">
                          {indexStatus.errors.map((error, index) => (
                            <div key={index} className="text-red-600 font-mono text-xs">
                              {error}
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              )}

              {/* Index Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={() => startIndexing(false)}
                  disabled={indexStatus?.status === 'indexing'}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
                >
                  Start Incremental Index
                </button>
                <button
                  onClick={() => startIndexing(true)}
                  disabled={indexStatus?.status === 'indexing'}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-300 transition-colors"
                >
                  Start Full Re-Index
                </button>
                {indexStatus?.status === 'indexing' && (
                  <button
                    onClick={stopIndexing}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Stop Indexing
                  </button>
                )}
              </div>

              {/* Database Stats */}
              {indexStats && (
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {indexStats.database.total_photos.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Total Photos</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {indexStats.database.indexed_photos.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Indexed</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {indexStats.database.photos_with_embeddings.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">With Embeddings</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {indexStats.database.total_faces.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Faces</div>
                  </div>
                </div>
              )}
            </section>

            {/* Advanced Features */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                🔧 Advanced Features
              </h2>

              <div className="space-y-4">
                {/* OCR Languages */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    OCR Languages
                  </label>
                  <p className="text-sm text-gray-600 mb-2">
                    Select languages for text extraction from images (requires Tesseract).
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'chi_sim', 'jpn', 'kor'].map((lang) => (
                      <label key={lang} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={ocrLanguages.includes(lang)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setOcrLanguages([...ocrLanguages, lang]);
                            } else {
                              setOcrLanguages(ocrLanguages.filter(l => l !== lang));
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{lang}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Face Search */}
                <div>
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={faceSearchEnabled}
                      onChange={(e) => setFaceSearchEnabled(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-700">Enable Face Search</span>
                      <p className="text-sm text-gray-600">
                        Enable face detection and recognition (requires additional dependencies).
                      </p>
                    </div>
                  </label>
                </div>
              </div>
            </section>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={saveConfig}
                disabled={saving}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors font-medium"
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <StatusBar />
    </div>
  );
}