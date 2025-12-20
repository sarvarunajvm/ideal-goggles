import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService, Person, SearchResult } from '../services/apiClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { AlertCircle, Search as SearchIcon, X } from 'lucide-react'
import { getThumbnailBaseUrl } from '../services/apiClient'

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([])
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [toast, setToast] = useState<{
    kind: 'Saved' | 'Deleted'
    id: number
  } | null>(null)
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(true)
  const [editingPersonId, setEditingPersonId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingPhotos, setLoadingPhotos] = useState(false)

  // Photo selection state
  const [indexedPhotos, setIndexedPhotos] = useState<SearchResult[]>([])
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<number[]>([])
  const [photoSearchQuery, setPhotoSearchQuery] = useState('')

  const navigate = useNavigate()

  // Load people list
  useEffect(() => {
    loadPeople()
  }, [])

  // Check face search config
  useEffect(() => {
    let cancelled = false
    const check = async () => {
      try {
        const cfg = await apiService.getConfig()
        if (!cancelled) setFaceSearchEnabled(!!cfg.face_search_enabled)
      } catch {
        // ignore
      }
    }
    check()
    const id = setInterval(check, 5000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const loadPeople = async () => {
    try {
      setLoading(true)
      const peopleData = await apiService.getPeople()
      setPeople(peopleData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load people')
    } finally {
      setLoading(false)
    }
  }

  const loadIndexedPhotos = async () => {
    try {
      setLoadingPhotos(true)
      const params: any = { limit: 200 }
      if (photoSearchQuery.trim()) {
        params.q = photoSearchQuery.trim()
      }
      const response = await apiService.searchPhotos(params)
      setIndexedPhotos(response.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load photos')
    } finally {
      setLoadingPhotos(false)
    }
  }

  useEffect(() => {
    if (showForm) {
      loadIndexedPhotos()
    }
  }, [showForm, photoSearchQuery])

  const resetForm = () => {
    setNameInput('')
    setSelectedPhotoIds([])
    setPhotoSearchQuery('')
    setEditingPersonId(null)
    setError(null)
  }

  const openAddForm = () => {
    resetForm()
    setShowForm(true)
  }

  const togglePhotoSelection = (photoId: number) => {
    setSelectedPhotoIds(prev => {
      if (prev.includes(photoId)) {
        return prev.filter(id => id !== photoId)
      }
      if (prev.length >= 10) {
        setError('Maximum 10 sample photos allowed')
        return prev
      }
      return [...prev, photoId]
    })
  }

  const savePerson = async () => {
    setError(null)
    if (!nameInput.trim()) {
      setError('Person name cannot be empty')
      return
    }
    if (selectedPhotoIds.length === 0) {
      setError('At least one photo is required')
      return
    }

    try {
      setLoading(true)

      if (editingPersonId) {
        // Update existing person
        await apiService.updatePerson(editingPersonId, {
          name: nameInput.trim(),
          additional_sample_file_ids: selectedPhotoIds,
        })
        setToast({ kind: 'Saved', id: editingPersonId })
      } else {
        // Create new person
        const newPerson = await apiService.createPerson(
          nameInput.trim(),
          selectedPhotoIds
        )
        setToast({ kind: 'Saved', id: newPerson.id })
      }

      await loadPeople()
      setShowForm(false)
      resetForm()
      setTimeout(() => setToast(null), 1200)
    } catch (err) {
      console.error('Save person error object:', err);
      const detailedError = (err as any).originalError ? `${(err as any).originalError}` : (err instanceof Error ? err.message : 'Failed to save person');
      setError(detailedError)
    } finally {
      setLoading(false)
    }
  }

  const selected = useMemo(
    () => people.find(p => p.id === selectedId) || null,
    [people, selectedId]
  )

  const deleteSelected = async () => {
    if (!selected) return

    try {
      setLoading(true)
      await apiService.deletePerson(selected.id)
      await loadPeople()
      setSelectedId(null)
      setToast({ kind: 'Deleted', id: selected.id })
      setTimeout(() => setToast(null), 1200)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete person')
    } finally {
      setLoading(false)
    }
  }

  const filteredPeople = useMemo(() => {
    const q = search.toLowerCase()
    return people.filter(p => p.name.toLowerCase().includes(q))
  }, [people, search])

  const selectedPhotos = useMemo(() => {
    return indexedPhotos.filter(p => selectedPhotoIds.includes(p.file_id))
  }, [indexedPhotos, selectedPhotoIds])

  return (
    <>
      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-foreground">People</h1>
            <Button
              onClick={openAddForm}
              disabled={loading}
              className="h-8 px-3 !bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-[1.02] !font-semibold transition-all disabled:opacity-50 disabled:hover:scale-100"
            >
              ➕ Add Person
            </Button>
          </div>

          {/* Search */}
          <div className="mb-6 flex items-center gap-3">
            <SearchIcon className="w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search people by name"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Add/Edit Form */}
          {showForm && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>
                  {editingPersonId ? 'Edit Person' : 'Add Person'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="person-name">Name</Label>
                    <Input
                      id="person-name"
                      placeholder="name"
                      value={nameInput}
                      onChange={e => setNameInput(e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label>Select Sample Photos ({selectedPhotoIds.length}/10)</Label>
                    <p className="text-sm text-muted-foreground mb-2">
                      Choose photos from your indexed library that contain this person
                    </p>

                    {/* Photo search */}
                    <div className="flex gap-2 mb-3">
                      <Input
                        placeholder="Search photos by filename..."
                        value={photoSearchQuery}
                        onChange={e => setPhotoSearchQuery(e.target.value)}
                      />
                    </div>

                    {/* Selected photos preview */}
                    {selectedPhotos.length > 0 && (
                      <div className="mb-3">
                        <p className="text-sm font-medium mb-2">Selected photos:</p>
                        <div className="grid grid-cols-5 gap-2" data-testid="photo-gallery">
                          {selectedPhotos.map(photo => (
                            <div key={photo.file_id} className="relative group">
                              <img
                                src={`${getThumbnailBaseUrl()}/${photo.thumb_path}`}
                                alt={photo.filename}
                                className="w-full aspect-square object-cover rounded border-2 border-primary"
                              />
                              <button
                                onClick={() => togglePhotoSelection(photo.file_id)}
                                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Available photos grid */}
                    {loadingPhotos ? (
                      <div className="text-center py-8 text-muted-foreground">
                        Loading photos...
                      </div>
                    ) : (
                      <div className="border rounded-lg p-3 max-h-96 overflow-y-auto">
                        <div className="grid grid-cols-6 gap-2">
                          {indexedPhotos.map(photo => {
                            const isSelected = selectedPhotoIds.includes(photo.file_id)
                            return (
                              <div
                                key={photo.file_id}
                                className={`relative cursor-pointer rounded transition ${
                                  isSelected ? 'ring-2 ring-primary' : 'hover:ring-1 hover:ring-primary/50'
                                }`}
                                onClick={() => togglePhotoSelection(photo.file_id)}
                              >
                                <img
                                  src={`${getThumbnailBaseUrl()}/${photo.thumb_path}`}
                                  alt={photo.filename}
                                  className="w-full aspect-square object-cover rounded"
                                />
                                {isSelected && (
                                  <div className="absolute inset-0 bg-primary/20 rounded flex items-center justify-center">
                                    <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                                      ✓
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                        {indexedPhotos.length === 0 && (
                          <div className="text-center py-8 text-muted-foreground">
                            No indexed photos found. Make sure your library is indexed first.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {error && (
                  <div
                    role="alert"
                    className="mt-3 flex items-center text-destructive text-sm"
                  >
                    <AlertCircle className="w-4 h-4 mr-2" />
                    {error}
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  <Button
                    onClick={savePerson}
                    disabled={!nameInput.trim() || selectedPhotoIds.length === 0 || loading}
                    className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
                  >
                    {loading ? 'Saving...' : 'Save Person'}
                  </Button>
                  <Button
                    variant="secondary"
                    className="!bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] transition-all"
                    onClick={() => {
                      setShowForm(false)
                      resetForm()
                    }}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* People List */}
          <div
            data-testid="people-list"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredPeople.map(person => (
              <Card
                key={person.id}
                data-testid="person-item"
                className="cursor-pointer border-border/50 hover:shadow-lg hover:shadow-[var(--shadow-gold)] hover:border-[rgb(var(--gold-rgb))]/30 transition-all duration-200 hover:-translate-y-1 bg-card/95 backdrop-blur"
                onClick={() => setSelectedId(person.id)}
              >
                <CardHeader className="text-center">
                  <div className="flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/30 rounded-full mx-auto mb-4">
                    <span className="text-2xl">👤</span>
                  </div>
                  <CardTitle className="text-lg text-foreground">{person.name}</CardTitle>
                  <CardDescription>
                    <span data-testid="photo-count">
                      {person.sample_count} sample photo
                      {person.sample_count !== 1 ? 's' : ''}
                    </span>
                    <br />
                    <span data-testid="enrolled-date">
                      Added {new Date(person.created_at).toLocaleDateString()}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <div className="flex justify-center mb-4">
                    <Badge
                      variant={person.active ? 'default' : 'secondary'}
                      className={person.active ? '!bg-gradient-to-r !from-[rgb(var(--purple-rgb))] !to-[rgb(var(--purple-rgb))] !text-white !border-[rgb(var(--purple-rgb))]/50 !shadow-[var(--shadow-purple)]' : ''}
                    >
                      {person.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <Button
                      onClick={e => {
                        e.stopPropagation()
                        if (faceSearchEnabled) {
                          navigate(`/?face=${person.id}`)
                        }
                      }}
                      className="w-full !bg-gradient-to-r !from-[rgb(var(--green-rgb))] !to-[rgb(var(--green-rgb))] hover:!from-[rgb(var(--green-rgb))]/80 hover:!to-[rgb(var(--green-rgb))]/80 !text-black !border-[rgb(var(--green-rgb))]/50 !shadow-[var(--shadow-green)] hover:!shadow-[var(--shadow-green)] hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
                      size="sm"
                      disabled={!faceSearchEnabled}
                    >
                      Find Photos!
                    </Button>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        className="flex-1 !bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 transition-all"
                        onClick={e => {
                          e.stopPropagation()
                          setEditingPersonId(person.id)
                          setNameInput(person.name)
                          setSelectedPhotoIds([])
                          setShowForm(true)
                        }}
                        disabled={loading}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 !bg-gradient-to-r !from-[rgb(var(--red-rgb))] !to-[rgb(var(--red-rgb))] hover:!from-[rgb(var(--red-rgb))]/80 hover:!to-[rgb(var(--red-rgb))]/80 !text-white !border-[rgb(var(--red-rgb))]/50 !shadow-[var(--shadow-red)] hover:!shadow-[var(--shadow-red)] hover:scale-105 transition-all"
                        onClick={e => {
                          e.stopPropagation()
                          setSelectedId(person.id)
                        }}
                        disabled={loading}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredPeople.length === 0 && !loading && (
            <div className="text-center py-16 text-muted-foreground">
              {search ? 'No people found matching your search' : 'No people enrolled yet'}
            </div>
          )}

          {loading && people.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              Loading people...
            </div>
          )}

          {/* Delete confirmation */}
          {selected && (
            <Card className="mt-6">
              <CardContent className="pt-4">
                <div className="font-medium mb-2">Delete {selected.name}?</div>
                <div className="flex gap-2">
                  <Button
                    className="bg-gradient-to-r from-[rgb(var(--red-rgb))] to-[rgb(var(--red-rgb))] hover:from-[rgb(var(--red-rgb))]/80 hover:to-[rgb(var(--red-rgb))]/80 text-white border-[rgb(var(--red-rgb))]/50 shadow-[var(--shadow-red)] hover:shadow-[var(--shadow-red)] transition-all"
                    onClick={deleteSelected}
                    disabled={loading}
                  >
                    Confirm Delete
                  </Button>
                  <Button
                    className="bg-gradient-to-r from-[rgb(var(--cyan-rgb))] to-[rgb(var(--cyan-rgb))] hover:from-[rgb(var(--cyan-rgb))]/80 hover:to-[rgb(var(--cyan-rgb))]/80 text-black border-[rgb(var(--cyan-rgb))]/50 shadow-[var(--shadow-cyan)] hover:shadow-[var(--shadow-cyan)] transition-all"
                    onClick={() => setSelectedId(null)}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Toast messages */}
          {toast && (
            <div
              role="alert"
              className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary to-yellow-300 text-black font-semibold px-6 py-3 rounded-full shadow-lg shadow-primary/50"
            >
              {toast.kind}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
