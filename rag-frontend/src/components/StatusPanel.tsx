import React, { useState, useEffect } from 'react'
import { Activity, Server, Database, Brain, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { apiClient } from '../lib/api'

interface SystemStatus {
  overall: boolean
  vectordb: boolean
  llm: boolean
  message: string
}

export function StatusPanel() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const checkStatus = async () => {
    try {
      setIsLoading(true)
      const [health, filesHealth] = await Promise.all([
        apiClient.getHealth(),
        apiClient.getFilesHealth()
      ])
      
      setStatus({
        overall: filesHealth.overall,
        vectordb: filesHealth.vectordb,
        llm: filesHealth.llm,
        message: health.message
      })
      setLastChecked(new Date())
    } catch (error) {
      console.error('Status check failed:', error)
      setStatus({
        overall: false,
        vectordb: false,
        llm: false,
        message: 'Status check failed'
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (isHealthy: boolean) => {
    if (isLoading) return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
    return isHealthy 
      ? <CheckCircle className="h-4 w-4 text-green-500" />
      : <XCircle className="h-4 w-4 text-red-500" />
  }

  const getStatusBadge = (isHealthy: boolean) => {
    return (
      <Badge variant={isHealthy ? "default" : "destructive"}>
        {isHealthy ? "Healthy" : "Unhealthy"}
      </Badge>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          System Status
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Overall System</span>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(status?.overall ?? false)}
            {getStatusBadge(status?.overall ?? false)}
          </div>
        </div>

        {/* Vector Database */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Vector Database</span>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(status?.vectordb ?? false)}
            {getStatusBadge(status?.vectordb ?? false)}
          </div>
        </div>

        {/* LLM Service */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">LLM Service</span>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon(status?.llm ?? false)}
            {getStatusBadge(status?.llm ?? false)}
          </div>
        </div>

        {/* Status Message */}
        {status?.message && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              {status.message}
            </p>
          </div>
        )}

        {/* Last Checked */}
        {lastChecked && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              Last checked: {lastChecked.toLocaleTimeString()}
            </p>
          </div>
        )}

        {/* Refresh Button */}
        <Button 
          variant="outline" 
          size="sm" 
          onClick={checkStatus}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Checking...
            </>
          ) : (
            'Refresh Status'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
