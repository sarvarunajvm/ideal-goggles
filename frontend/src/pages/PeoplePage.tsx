import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/apiClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Upload, AlertCircle, Search as SearchIcon } from 'lucide-react'

type Person = {
  id: number
  name: string
  createdAt: string
  active: boolean
  photos: string[]
}

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([])
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [formPhotos, setFormPhotos] = useState<string[]>([])
  const [toast, setToast] = useState<{
    kind: 'Saved' | 'Deleted'
    id: number
  } | null>(null)
  const [faceSearchEnabled, setFaceSearchEnabled] = useState(true)
  const [photoToRemove, setPhotoToRemove] = useState<{
    personId: number
    photoIndex: number
  } | null>(null)
  const [editingPersonId, setEditingPersonId] = useState<number | null>(null)
  const navigate = useNavigate()

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

  const resetForm = () => {
    setNameInput('')
    setFormPhotos([])
    setEditingPersonId(null)
  }

  const openAddForm = () => {
    resetForm()
    setShowForm(true)
  }

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return
    const urls: string[] = []
    for (const f of Array.from(files)) {
      const url = URL.createObjectURL(f)
      urls.push(url)
    }
    setFormPhotos(prev => [...prev, ...urls])
  }

  const savePerson = () => {
    setError(null)
    if (!nameInput.trim()) {
      setError('Person name cannot be empty')
      return
    }
    // Allow saving without photos - photos can be added later

    if (editingPersonId) {
      // Update existing person
      setPeople(prev =>
        prev.map(p =>
          p.id === editingPersonId
            ? { ...p, name: nameInput.trim(), photos: formPhotos }
            : p
        )
      )
      setToast({ kind: 'Saved', id: editingPersonId })
    } else {
      // Create new person
      const now = new Date().toISOString()
      const newPerson: Person = {
        id: Date.now(),
        name: nameInput.trim(),
        createdAt: now,
        active: true,
        photos: formPhotos,
      }
      setPeople(prev => [...prev, newPerson])
      setToast({ kind: 'Saved', id: newPerson.id })
    }

    setShowForm(false)
    resetForm()
    setTimeout(() => setToast(null), 1200)
  }

  const selected = useMemo(
    () => people.find(p => p.id === selectedId) || null,
    [people, selectedId]
  )

  const updateSelected = (updater: (p: Person) => Person) => {
    if (!selected) return
    setPeople(prev => prev.map(p => (p.id === selected.id ? updater(p) : p)))
    setToast({ kind: 'Saved', id: selected.id })
    setTimeout(() => setToast(null), 1200)
  }

  const confirmRemovePhoto = () => {
    if (!photoToRemove) return
    const person = people.find(p => p.id === photoToRemove.personId)
    if (!person) return

    setPeople(prev =>
      prev.map(p =>
        p.id === photoToRemove.personId
          ? {
              ...p,
              photos: p.photos.filter((_, i) => i !== photoToRemove.photoIndex),
            }
          : p
      )
    )
    setPhotoToRemove(null)
    setToast({ kind: 'Saved', id: photoToRemove.personId })
    setTimeout(() => setToast(null), 1200)
  }

  const deleteSelected = () => {
    if (!selected) return
    setPeople(prev => prev.filter(p => p.id !== selected.id))
    setSelectedId(null)
    setToast({ kind: 'Deleted', id: selected.id })
    setTimeout(() => setToast(null), 1200)
  }

  const filteredPeople = useMemo(() => {
    const q = search.toLowerCase()
    return people.filter(p => p.name.toLowerCase().includes(q))
  }, [people, search])

  return (
    <>
      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-foreground">People</h1>
            <Button onClick={openAddForm}>➕ Add Person</Button>
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                    <Label>Photos</Label>
                    <div className="relative">
                      <Button
                        type="button"
                        variant="secondary"
                        className="mr-2"
                        onClick={() =>
                          document.getElementById('new-person-file')?.click()
                        }
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Photos
                      </Button>
                      <input
                        id="new-person-file"
                        type="file"
                        multiple
                        className="hidden"
                        onChange={e => handleFileSelect(e.target.files)}
                      />
                    </div>
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
                    disabled={!nameInput.trim()}
                  >
                    Save Person
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setShowForm(false)
                      resetForm()
                    }}
                  >
                    Cancel
                  </Button>
                </div>
                {formPhotos.length > 0 && (
                  <div className="mt-4" data-testid="photo-gallery">
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                      {formPhotos.map((src, idx) => (
                        <img
                          key={idx}
                          src={src}
                          alt="preview"
                          className="w-full aspect-square object-cover rounded"
                        />
                      ))}
                    </div>
                  </div>
                )}
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
                className="cursor-pointer border-border/50 hover:shadow-lg hover:shadow-primary/10 hover:border-primary/30 transition-all duration-200 hover:-translate-y-1"
                onClick={() => setSelectedId(person.id)}
              >
                <CardHeader className="text-center">
                  <div className="flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/30 rounded-full mx-auto mb-4">
                    <span className="text-2xl">👤</span>
                  </div>
                  <CardTitle className="text-lg text-foreground">{person.name}</CardTitle>
                  <CardDescription>
                    <span data-testid="photo-count">
                      {person.photos.length} sample photo
                      {person.photos.length !== 1 ? 's' : ''}
                    </span>
                    <br />
                    <span data-testid="enrolled-date">
                      Added {new Date(person.createdAt).toLocaleDateString()}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <div className="flex justify-center mb-4">
                    <Badge variant={person.active ? 'default' : 'secondary'}>
                      {person.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <Button
                      onClick={e => {
                        e.stopPropagation()
                        setSelectedId(person.id)
                        if (faceSearchEnabled) {
                          navigate(`/?face=${person.id}`)
                        }
                      }}
                      className="w-full"
                      size="sm"
                      disabled={!faceSearchEnabled}
                    >
                      Search Photos of this Person
                    </Button>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={e => {
                          e.stopPropagation()
                          setSelectedId(person.id)
                          setEditingPersonId(person.id)
                          setShowForm(true)
                          setNameInput(person.name)
                          setFormPhotos(person.photos)
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        className="flex-1"
                        onClick={e => {
                          e.stopPropagation()
                          setSelectedId(person.id)
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>

                {selectedId === person.id && (
                  <CardFooter className="flex-col items-start border-t pt-4">
                    <div className="w-full">
                      <div className="flex items-center justify-between mb-2">
                        <Label>Photos</Label>
                        <div>
                          <Button
                            variant="secondary"
                            onClick={e => {
                              e.stopPropagation()
                              document
                                .getElementById(`file-${person.id}`)
                                ?.click()
                            }}
                          >
                            <Upload className="w-4 h-4 mr-2" /> Upload Photos
                          </Button>
                          <input
                            id={`file-${person.id}`}
                            type="file"
                            multiple
                            className="hidden"
                            onChange={e => {
                              const files = e.target.files
                              if (!files) return
                              const urls: string[] = []
                              for (const f of Array.from(files)) {
                                const url = URL.createObjectURL(f)
                                urls.push(url)
                              }
                              updateSelected(p => ({
                                ...p,
                                photos: [...p.photos, ...urls],
                              }))
                            }}
                          />
                          <Button
                            className="ml-2"
                            onClick={e => {
                              e.stopPropagation()
                              // The photos have already been added via updateSelected in the file input onChange
                              setToast({ kind: 'Saved', id: person.id })
                              setTimeout(() => setToast(null), 1200)
                            }}
                          >
                            Save Person
                          </Button>
                        </div>
                      </div>
                    </div>
                    <div
                      data-testid="photo-gallery"
                      className="grid grid-cols-3 gap-2 w-full"
                    >
                      {person.photos.map((src, idx) => (
                        <div key={idx} className="relative group">
                          <img
                            src={src}
                            alt="photo"
                            className="w-full aspect-square object-cover rounded"
                          />
                          <Button
                            data-testid="remove-photo"
                            variant="secondary"
                            size="sm"
                            className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition h-auto py-0.5 px-2 text-xs"
                            onClick={e => {
                              e.stopPropagation()
                              setPhotoToRemove({
                                personId: person.id,
                                photoIndex: idx,
                              })
                            }}
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardFooter>
                )}
              </Card>
            ))}
          </div>

          {/* Delete confirmation */}
          {selected && (
            <Card className="mt-6">
              <CardContent className="pt-4">
                <div className="font-medium mb-2">Delete {selected.name}?</div>
                <div className="flex gap-2">
                  <Button variant="destructive" onClick={deleteSelected}>
                    Confirm Delete
                  </Button>
                  <Button variant="ghost" onClick={() => setSelectedId(null)}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Photo removal confirmation */}
          {photoToRemove && (
            <Card className="mt-6">
              <CardContent className="pt-4">
                <div className="font-medium mb-2">Remove this photo?</div>
                <div className="flex gap-2">
                  <Button
                    id="confirm-remove-btn"
                    variant="destructive"
                    onClick={confirmRemovePhoto}
                  >
                    Confirm
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => setPhotoToRemove(null)}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Toast messages expected by tests */}
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
