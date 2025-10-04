import { useState, useEffect } from 'react'
import { apiService } from '../services/apiClient'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Image, Users, FileText, Search, Database, Activity, TrendingUp, Loader2 } from 'lucide-react'

interface IndexStats {
  database: {
    total_photos: number
    indexed_photos: number
    photos_with_embeddings: number
    total_faces: number
  }
}

export default function StatsPage() {
  const [stats, setStats] = useState<IndexStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true)
        const statsData = await apiService.getIndexStats()
        setStats(statsData as unknown as IndexStats)
      } catch (error) {
        console.error('Failed to load stats:', error)
      } finally {
        setLoading(false)
      }
    }

    loadStats()
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Database className="h-12 w-12 mx-auto text-muted-foreground" />
          <p className="text-muted-foreground">No statistics available</p>
        </div>
      </div>
    )
  }

  const indexedPercentage = stats.database.total_photos > 0
    ? (stats.database.indexed_photos / stats.database.total_photos) * 100
    : 0

  const searchablePercentage = stats.database.total_photos > 0
    ? (stats.database.photos_with_embeddings / stats.database.total_photos) * 100
    : 0

  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="w-full max-w-[1920px] mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-2">
            <Activity className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Library Statistics</h1>
          </div>
          <p className="text-muted-foreground">
            Overview of your photo library and indexing progress
          </p>
        </div>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          {/* Total Photos */}
          <Card className="border-primary/30 bg-gradient-to-br from-primary/10 to-primary/5 hover:shadow-lg hover:shadow-primary/20 transition-all">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Photos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold text-primary">
                  {stats.database.total_photos.toLocaleString()}
                </div>
                <Image className="h-8 w-8 text-primary/50" />
              </div>
            </CardContent>
          </Card>

          {/* Indexed Photos */}
          <Card className="border-green-500/30 bg-gradient-to-br from-green-500/10 to-green-500/5 hover:shadow-lg hover:shadow-green-500/20 transition-all">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Indexed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold text-green-400">
                  {stats.database.indexed_photos.toLocaleString()}
                </div>
                <FileText className="h-8 w-8 text-green-400/50" />
              </div>
              <Progress value={indexedPercentage} className="h-1 mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {indexedPercentage.toFixed(1)}% complete
              </p>
            </CardContent>
          </Card>

          {/* Searchable Photos */}
          <Card className="border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-blue-500/5 hover:shadow-lg hover:shadow-blue-500/20 transition-all">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Searchable
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold text-blue-400">
                  {stats.database.photos_with_embeddings.toLocaleString()}
                </div>
                <Search className="h-8 w-8 text-blue-400/50" />
              </div>
              <Progress value={searchablePercentage} className="h-1 mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {searchablePercentage.toFixed(1)}% searchable
              </p>
            </CardContent>
          </Card>

          {/* Faces Detected */}
          <Card className="border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-purple-500/5 hover:shadow-lg hover:shadow-purple-500/20 transition-all">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Faces Detected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-3xl font-bold text-purple-400">
                  {stats.database.total_faces.toLocaleString()}
                </div>
                <Users className="h-8 w-8 text-purple-400/50" />
              </div>
              {stats.database.indexed_photos > 0 && (
                <p className="text-xs text-muted-foreground mt-2">
                  ~{(stats.database.total_faces / stats.database.indexed_photos).toFixed(1)} per photo
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Detailed Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Processing Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                <span>Processing Overview</span>
              </CardTitle>
              <CardDescription>
                Current state of your photo library
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">Photos Found</span>
                    <span className="text-sm text-muted-foreground">
                      {stats.database.total_photos.toLocaleString()}
                    </span>
                  </div>
                  <Progress value={100} className="h-2" />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">Metadata Extracted</span>
                    <span className="text-sm text-muted-foreground">
                      {stats.database.indexed_photos.toLocaleString()}
                    </span>
                  </div>
                  <Progress value={indexedPercentage} className="h-2" />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">Made Searchable</span>
                    <span className="text-sm text-muted-foreground">
                      {stats.database.photos_with_embeddings.toLocaleString()}
                    </span>
                  </div>
                  <Progress value={searchablePercentage} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5 text-primary" />
                <span>Quick Stats</span>
              </CardTitle>
              <CardDescription>
                Key metrics at a glance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Pending Processing</p>
                  <p className="text-2xl font-bold text-orange-400">
                    {(stats.database.total_photos - stats.database.indexed_photos).toLocaleString()}
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Not Searchable</p>
                  <p className="text-2xl font-bold text-red-400">
                    {(stats.database.indexed_photos - stats.database.photos_with_embeddings).toLocaleString()}
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Avg Faces/Photo</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {stats.database.indexed_photos > 0
                      ? (stats.database.total_faces / stats.database.indexed_photos).toFixed(2)
                      : '0'}
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Library Health</p>
                  <div className="flex items-center space-x-2">
                    <p className="text-2xl font-bold text-green-400">
                      {searchablePercentage.toFixed(0)}%
                    </p>
                    <Badge variant={searchablePercentage > 80 ? "default" : searchablePercentage > 50 ? "secondary" : "destructive"}>
                      {searchablePercentage > 80 ? "Good" : searchablePercentage > 50 ? "Fair" : "Poor"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
