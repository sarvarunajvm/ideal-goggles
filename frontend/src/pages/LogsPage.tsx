/**
 * LogsPage - System Logs View
 * Provides access to unified logging viewer for debugging
 */

import { LogViewer } from '../components/LogViewer'

export function LogsPage() {
  return (
    <div className="h-screen flex flex-col">
      <LogViewer />
    </div>
  )
}
