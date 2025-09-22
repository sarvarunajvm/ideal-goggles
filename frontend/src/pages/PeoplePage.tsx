import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Navigation from '../components/Navigation';
import StatusBar from '../components/StatusBar';

interface Person {
  id: number;
  name: string;
  sample_count: number;
  created_at: string;
  active: boolean;
}

export default function PeoplePage() {
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPeople();
  }, []);

  const loadPeople = async () => {
    try {
      setLoading(true);
      const peopleData = await apiService.getPeople();
      setPeople(peopleData as unknown as Person[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load people');
    } finally {
      setLoading(false);
    }
  };

  const searchForPerson = async (personId: number) => {
    try {
      await apiService.searchFaces(personId);
      // TODO: Navigate to search results page with results
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Face search failed');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Navigation />

      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-gray-900">People</h1>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              ➕ Add Person
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <span className="text-red-600 mr-2">❌</span>
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading people...</p>
              </div>
            </div>
          ) : people.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">👥</div>
              <h2 className="text-2xl font-semibold text-gray-700 mb-2">No people enrolled</h2>
              <p className="text-gray-500 mb-6">
                Add people to enable face-based photo search.
              </p>
              <div className="max-w-md mx-auto text-left">
                <h3 className="font-medium text-gray-900 mb-2">To get started:</h3>
                <ol className="text-sm text-gray-600 space-y-1">
                  <li>1. Enable face search in Settings</li>
                  <li>2. Index your photos</li>
                  <li>3. Add people using sample photos</li>
                  <li>4. Search for photos containing specific people</li>
                </ol>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {people.map((person) => (
                <div
                  key={person.id}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
                >
                  {/* Person Avatar */}
                  <div className="flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mx-auto mb-4">
                    <span className="text-2xl">👤</span>
                  </div>

                  {/* Person Info */}
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {person.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-1">
                      {person.sample_count} sample photo{person.sample_count !== 1 ? 's' : ''}
                    </p>
                    <p className="text-xs text-gray-500 mb-4">
                      Added {new Date(person.created_at).toLocaleDateString()}
                    </p>

                    {/* Status */}
                    <div className="flex justify-center mb-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        person.active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {person.active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="space-y-2">
                      <button
                        onClick={() => searchForPerson(person.id)}
                        className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                      >
                        🔍 Find Photos
                      </button>
                      <div className="flex space-x-2">
                        <button className="flex-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm">
                          ✏️ Edit
                        </button>
                        <button className="flex-1 px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm">
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <StatusBar />
    </div>
  );
}