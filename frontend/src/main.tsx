import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  createBrowserRouter,
  createHashRouter,
  RouterProvider,
} from 'react-router-dom'
import App from './App'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'
import PeoplePage from './pages/PeoplePage'
import './index.css'

// Disable context menu in production
if (process.env.NODE_ENV === 'production') {
  document.addEventListener('contextmenu', e => e.preventDefault())
}

// Create router with future flags enabled
const createRouter =
  process.env.NODE_ENV === 'production' ? createHashRouter : createBrowserRouter

const router = createRouter(
  [
    {
      path: '/',
      element: <App />,
      children: [
        {
          index: true,
          element: <SearchPage />,
        },
        {
          path: 'settings',
          element: <SettingsPage />,
        },
        {
          path: 'people',
          element: <PeoplePage />,
        },
      ],
    },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true,
    },
  }
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
