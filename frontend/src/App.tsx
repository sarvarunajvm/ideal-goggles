import { Routes, Route } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'
import PeoplePage from './pages/PeoplePage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/people" element={<PeoplePage />} />
      </Routes>
    </div>
  )
}

export default App