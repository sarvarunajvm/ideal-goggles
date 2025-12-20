/**
 * LogsPage - System Logs View
 * Provides access to unified logging viewer for debugging
 */

import { LogViewer } from '../components/LogViewer'
import { FileText } from 'lucide-react'

export function LogsPage() {
  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="w-full max-w-[1920px] mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <FileText className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">System Logs</h1>
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 gap-6">
          <LogViewer />
        </div>
      </div>
    </div>
  )
}
