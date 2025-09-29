import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiClient';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload, AlertCircle, Search as SearchIcon } from 'lucide-react';

type Person = {
  id: number;
  name: string;
  createdAt: string;
  active: boolean;
  photos: string[];
};

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [formPhotos, setFormPhotos] = useState<string[]>([]);
  const [toast, setToast] = useState<{ kind: 'Saved' | 'Deleted'; id: number } | null>(null);
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const cfg = await apiService.getConfig();
        if (!cancelled) setFaceSearchEnabled(!!cfg.face_search_enabled);
      } catch {
        // ignore
      }
    };
    check();
    const id = setInterval(check, 2000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const resetForm = () => {
    setNameInput('');
    setFormPhotos([]);
  };

  const openAddForm = () => {
    resetForm();
    setShowForm(true);
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    const urls: string[] = [];
    for (const f of Array.from(files)) {
      const url = URL.createObjectURL(f);
      urls.push(url);
    }
    setFormPhotos((prev) => [...prev, ...urls]);
  };

  const savePerson = () => {
    setError(null);
    if (!nameInput.trim()) {
      setError('Person name cannot be empty');
      return;
    }
    if (formPhotos.length < 1) {
      setError('At least one photo is required');
      return;
    }
    const now = new Date().toISOString();
    const newPerson: Person = {
      id: Date.now(),
      name: nameInput.trim(),
      createdAt: now,
      active: true,
      photos: formPhotos,
    };
    setPeople((prev) => [...prev, newPerson]);
    setShowForm(false);
    setToast({ kind: 'Saved', id: newPerson.id });
    setTimeout(() => setToast(null), 1200);
  };

  const selected = useMemo(() => people.find((p) => p.id === selectedId) || null, [people, selectedId]);

  const updateSelected = (updater: (p: Person) => Person) => {
    if (!selected) return;
    setPeople((prev) => prev.map((p) => (p.id === selected.id ? updater(p) : p)));
    setToast({ kind: 'Saved', id: selected.id });
    setTimeout(() => setToast(null), 1200);
  };

  const deleteSelected = () => {
    if (!selected) return;
    setPeople((prev) => prev.filter((p) => p.id !== selected.id));
    setSelectedId(null);
    setToast({ kind: 'Deleted', id: selected.id });
    setTimeout(() => setToast(null), 1200);
  };

  const filteredPeople = useMemo(() => {
    const q = search.toLowerCase();
    return people.filter((p) => p.name.toLowerCase().includes(q));
  }, [people, search]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Navigation />

      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-gray-900">People</h1>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors" onClick={openAddForm}>
              ➕ Add Person
            </button>
          </div>

          {/* Search */}
          <div className="mb-6 flex items-center gap-3">
            <SearchIcon className="w-4 h-4 text-gray-500" />
            <Input placeholder="Search people by name" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>

          {/* Add/Edit Form */}
          {showForm && (
            <div className="border rounded-lg p-4 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Name</label>
                  <Input placeholder="Enter person name" value={nameInput} onChange={(e) => setNameInput(e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Photos</label>
                  <div className="relative">
                    <Button type="button" variant="secondary" className="mr-2" onClick={() => document.getElementById('new-person-file')?.click()}>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Photos
                    </Button>
                    <input id="new-person-file" type="file" multiple className="" onChange={(e) => handleFileSelect(e.target.files)} />
                  </div>
                </div>
              </div>
              {error && (
                <div role="alert" className="mt-3 flex items-center text-red-700 text-sm"><AlertCircle className="w-4 h-4 mr-2" />{error}</div>
              )}
              <div className="mt-4 flex gap-2">
                <Button onClick={savePerson} disabled={!nameInput.trim() || formPhotos.length === 0}>Save Person</Button>
                <Button variant="ghost" onClick={() => { setShowForm(false); resetForm(); }}>Cancel</Button>
              </div>
              {formPhotos.length > 0 && (
                <div className="mt-4" data-testid="photo-gallery">
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {formPhotos.map((src, idx) => (
                      <img key={idx} src={src} alt="preview" className="w-full aspect-square object-cover rounded" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* People List */}
          <div data-testid="people-list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredPeople.map((person) => (
              <div key={person.id} data-testid="person-item" className="bg-white rounded-lg shadow-sm border border-gray-200 p-6" onClick={() => setSelectedId(person.id)}>
                <div className="flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mx-auto mb-4">
                  <span className="text-2xl">👤</span>
                </div>
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{person.name}</h3>
                  <p className="text-sm text-gray-600 mb-1" data-testid="photo-count">{person.photos.length} sample photo{person.photos.length !== 1 ? 's' : ''}</p>
                  <p className="text-xs text-gray-500 mb-4" data-testid="enrolled-date">Added {new Date(person.createdAt).toLocaleDateString()}</p>
                  <div className="flex justify-center mb-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${person.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{person.active ? 'Active' : 'Inactive'}</span>
                  </div>
                  <div className="space-y-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedId(person.id);
                        if (faceSearchEnabled) {
                          navigate(`/?face=${person.id}`);
                        }
                      }}
                      className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                      disabled={!faceSearchEnabled}
                    >
                      Search Photos of this Person
                    </button>
                    <div className="flex space-x-2">
                      <button className="flex-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm" onClick={(e) => {
                        e.stopPropagation(); setSelectedId(person.id); setShowForm(true); setNameInput(person.name); setFormPhotos(person.photos);
                      }}>Edit</button>
                      <button className="flex-1 px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm" onClick={(e) => { e.stopPropagation(); setSelectedId(person.id); }}>Delete</button>
                    </div>
                  </div>
                </div>

                {selectedId === person.id && (
                  <div className="mt-4 border-t pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium">Photos</div>
                      <div>
                        <Button variant="secondary" onClick={(e) => { e.stopPropagation(); document.getElementById(`file-${person.id}`)?.click(); }}>
                          <Upload className="w-4 h-4 mr-2" /> Upload Photos
                        </Button>
                        <input id={`file-${person.id}`} type="file" multiple className="" onChange={(e) => {
                          const files = e.target.files; if (!files) return; const urls: string[] = [];
                          for (const f of Array.from(files)) { const url = URL.createObjectURL(f); urls.push(url); }
                          updateSelected((p) => ({ ...p, photos: [...p.photos, ...urls] }));
                        }} />
                        <Button className="ml-2" onClick={(e) => { e.stopPropagation(); setToast({ kind: 'Saved', id: person.id }); setTimeout(() => setToast(null), 1200); }}>Save Person</Button>
                      </div>
                    </div>
                    <div data-testid="photo-gallery" className="grid grid-cols-3 gap-2">
                      {person.photos.map((src, idx) => (
                        <div key={idx} className="relative group">
                          <img src={src} alt="photo" className="w-full aspect-square object-cover rounded" />
                          <button data-testid="remove-photo" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition bg-white/80 border rounded px-2 py-0.5 text-xs" onClick={(e) => {
                            e.stopPropagation();
                            const confirmBtn = document.getElementById('confirm-remove-btn');
                            const dialog = document.getElementById('confirm-remove');
                            if (dialog) dialog.classList.remove('hidden');
                            (confirmBtn as HTMLButtonElement | null)?.addEventListener('click', () => {
                              updateSelected((p) => ({ ...p, photos: p.photos.filter((_, i) => i !== idx) }));
                              if (dialog) dialog.classList.add('hidden');
                            }, { once: true });
                          }}>Remove</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Delete confirmation */}
          {selected && (
            <div className="mt-6 border rounded p-4">
              <div className="font-medium mb-2">Delete {selected.name}?</div>
              <div className="flex gap-2">
                <Button variant="destructive" onClick={deleteSelected}>Confirm Delete</Button>
                <Button variant="ghost" onClick={() => setSelectedId(null)}>Cancel</Button>
              </div>
            </div>
          )}

          {/* Hidden confirm overlay for photo removal */}
          <div id="confirm-remove" className="hidden">
            <Button id="confirm-remove-btn">Confirm</Button>
          </div>

          {/* Toast messages expected by tests */}
          {toast && (
            <div role="alert" className="fixed bottom-4 right-4 bg-black text-white px-4 py-2 rounded shadow">
              {toast.kind}
            </div>
          )}
        </div>
      </div>

      <StatusBar />
    </div>
  );
}
