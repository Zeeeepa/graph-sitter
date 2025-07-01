"use client"

import { useState } from "react"
import { BarChart3, Code2, FileCode2, GitBranch, Github, Settings, MessageSquare, FileText, Code, RefreshCcw, PaintBucket, Brain, TreePine, AlertTriangle, AlertCircle, Info } from "lucide-react"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from "recharts"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TreeView, IssueList } from "@/components/ui/tree-view"

interface IssueDetail {
  severity: string
  type: string
  description: string
  file_path: string
  line_number?: number
  context_lines?: string[]
  suggestion?: string
}

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  issue_count: number
  critical_issues: number
  functional_issues: number
  minor_issues: number
  children?: FileNode[]
  issues?: IssueDetail[]
}

interface EnhancedRepoAnalysis {
  repo_url: string
  description: string
  basic_metrics: {
    files: number
    functions: number
    classes: number
    modules: number
  }
  line_metrics: {
    total: {
      loc: number
      lloc: number
      sloc: number
      comments: number
      comment_density: number
    }
  }
  complexity_metrics: {
    cyclomatic_complexity: { average: number }
    depth_of_inheritance: { average: number }
    halstead_metrics: { total_volume: number; average_volume: number }
    maintainability_index: { average: number }
  }
  repository_structure: FileNode
  issues_summary: {
    total: number
    critical: number
    functional: number
    minor: number
  }
  detailed_issues: IssueDetail[]
  monthly_commits?: { [key: string]: number }
}

const SEVERITY_COLORS = {
  Critical: "#ef4444",
  Functional: "#f97316", 
  Minor: "#eab308"
}

export default function RepoAnalyticsDashboard() {
  const [repoUrl, setRepoUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<EnhancedRepoAnalysis | null>(null)
  const [error, setError] = useState("")
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)

  const analyzeRepo = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL")
      return
    }

    setLoading(true)
    setError("")
    setData(null)

    try {
      // Use localhost for local development
      const response = await fetch('http://localhost:8000/analyze_repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (node: FileNode) => {
    setSelectedFile(node)
  }

  const issueChartData = data ? [
    { name: 'Critical', value: data.issues_summary.critical, color: SEVERITY_COLORS.Critical },
    { name: 'Functional', value: data.issues_summary.functional, color: SEVERITY_COLORS.Functional },
    { name: 'Minor', value: data.issues_summary.minor, color: SEVERITY_COLORS.Minor },
  ].filter(item => item.value > 0) : []

  const commitChartData = data?.monthly_commits ? 
    Object.entries(data.monthly_commits)
      .map(([month, commits]) => ({ month, commits }))
      .sort((a, b) => a.month.localeCompare(b.month))
      .slice(-12) // Last 12 months
    : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Enhanced Codebase Analytics
            </h1>
          </div>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Powered by Graph-Sitter • Advanced code analysis with interactive issue detection and repository exploration
          </p>
        </div>

        {/* Input Section */}
        <Card className="border-2 border-dashed border-slate-300 bg-white/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Github className="h-5 w-5" />
              Repository Analysis
            </CardTitle>
            <CardDescription>
              Enter a GitHub repository URL (e.g., "owner/repo") to analyze code quality, complexity, and detect issues
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="e.g., facebook/react or https://github.com/facebook/react"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && analyzeRepo()}
                className="flex-1"
              />
              <Button 
                onClick={analyzeRepo} 
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {loading ? (
                  <>
                    <RefreshCcw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Analyze Repository
                  </>
                )}
              </Button>
            </div>
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {data && (
          <div className="space-y-6">
            {/* Repository Header */}
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl flex items-center gap-2">
                      <Github className="h-6 w-6" />
                      {data.repo_url}
                    </CardTitle>
                    <CardDescription className="text-base mt-2">
                      {data.description || "No description available"}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {data.issues_summary.critical > 0 && (
                      <Badge variant="destructive" className="text-sm">
                        ⚠️ {data.issues_summary.critical} Critical
                      </Badge>
                    )}
                    {data.issues_summary.functional > 0 && (
                      <Badge variant="secondary" className="text-sm bg-orange-100 text-orange-800">
                        🐞 {data.issues_summary.functional} Functional
                      </Badge>
                    )}
                    {data.issues_summary.minor > 0 && (
                      <Badge variant="outline" className="text-sm bg-yellow-100 text-yellow-800">
                        🔍 {data.issues_summary.minor} Minor
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Main Content Tabs */}
            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">📊 Overview</TabsTrigger>
                <TabsTrigger value="structure">🌳 Repository Structure</TabsTrigger>
                <TabsTrigger value="issues">🔍 Issues Analysis</TabsTrigger>
                <TabsTrigger value="metrics">📈 Detailed Metrics</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Files</CardTitle>
                      <FileCode2 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{data.basic_metrics.files.toLocaleString()}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Functions</CardTitle>
                      <Code className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{data.basic_metrics.functions.toLocaleString()}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Classes</CardTitle>
                      <Settings className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{data.basic_metrics.classes.toLocaleString()}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Issues</CardTitle>
                      <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-red-600">{data.issues_summary.total}</div>
                    </CardContent>
                  </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Issue Distribution Chart */}
                  {issueChartData.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Issue Distribution</CardTitle>
                        <CardDescription>Breakdown of issues by severity</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={200}>
                          <PieChart>
                            <Pie
                              data={issueChartData}
                              cx="50%"
                              cy="50%"
                              innerRadius={40}
                              outerRadius={80}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {issueChartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  )}

                  {/* Commit Activity */}
                  {commitChartData.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Commit Activity</CardTitle>
                        <CardDescription>Monthly commit frequency</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={200}>
                          <BarChart data={commitChartData}>
                            <XAxis dataKey="month" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="commits" fill="#3b82f6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </TabsContent>

              {/* Repository Structure Tab */}
              <TabsContent value="structure" className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TreePine className="h-5 w-5" />
                        Interactive Repository Structure
                      </CardTitle>
                      <CardDescription>
                        Click on folders to expand/collapse. Click on files to view their issues.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="max-h-96 overflow-y-auto">
                      <TreeView 
                        node={data.repository_structure} 
                        onFileSelect={handleFileSelect}
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>File Details</CardTitle>
                      <CardDescription>
                        {selectedFile ? `Issues in ${selectedFile.name}` : "Select a file to view details"}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {selectedFile ? (
                        <div className="space-y-3">
                          <div className="text-sm text-gray-600">
                            <strong>Path:</strong> {selectedFile.path}
                          </div>
                          <div className="text-sm text-gray-600">
                            <strong>Type:</strong> {selectedFile.type}
                          </div>
                          <div className="flex gap-2">
                            {selectedFile.critical_issues > 0 && (
                              <Badge variant="destructive" className="text-xs">
                                ⚠️ {selectedFile.critical_issues}
                              </Badge>
                            )}
                            {selectedFile.functional_issues > 0 && (
                              <Badge variant="secondary" className="text-xs bg-orange-100 text-orange-800">
                                🐞 {selectedFile.functional_issues}
                              </Badge>
                            )}
                            {selectedFile.minor_issues > 0 && (
                              <Badge variant="outline" className="text-xs bg-yellow-100 text-yellow-800">
                                🔍 {selectedFile.minor_issues}
                              </Badge>
                            )}
                          </div>
                          {selectedFile.issues && selectedFile.issues.length > 0 && (
                            <div className="mt-4">
                              <h4 className="font-medium mb-2">Issues:</h4>
                              <div className="space-y-2 max-h-48 overflow-y-auto">
                                {selectedFile.issues.map((issue, index) => (
                                  <div key={index} className="text-xs p-2 bg-gray-50 rounded border-l-2 border-l-red-200">
                                    <div className="font-medium">{issue.type}</div>
                                    <div className="text-gray-600">{issue.description}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">Click on a file in the tree to view its details and issues.</p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Issues Analysis Tab */}
              <TabsContent value="issues" className="space-y-4">
                <IssueList 
                  issues={data.detailed_issues} 
                  title={`All Issues (${data.detailed_issues.length})`}
                />
              </TabsContent>

              {/* Detailed Metrics Tab */}
              <TabsContent value="metrics" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Line Metrics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between">
                        <span>Lines of Code:</span>
                        <span className="font-mono">{data.line_metrics.total.loc.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Logical Lines:</span>
                        <span className="font-mono">{data.line_metrics.total.lloc.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Source Lines:</span>
                        <span className="font-mono">{data.line_metrics.total.sloc.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Comments:</span>
                        <span className="font-mono">{data.line_metrics.total.comments.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Comment Density:</span>
                        <span className="font-mono">{data.line_metrics.total.comment_density.toFixed(1)}%</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Complexity Metrics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between">
                        <span>Avg. Cyclomatic Complexity:</span>
                        <span className="font-mono">{data.complexity_metrics.cyclomatic_complexity.average.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg. Maintainability Index:</span>
                        <span className="font-mono">{data.complexity_metrics.maintainability_index.average}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg. Depth of Inheritance:</span>
                        <span className="font-mono">{data.complexity_metrics.depth_of_inheritance.average.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Halstead Volume:</span>
                        <span className="font-mono">{data.complexity_metrics.halstead_metrics.total_volume.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg. Halstead Volume:</span>
                        <span className="font-mono">{data.complexity_metrics.halstead_metrics.average_volume.toLocaleString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </div>
  )
}

