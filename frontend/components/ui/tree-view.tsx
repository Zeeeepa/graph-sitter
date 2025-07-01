"use client"

import React, { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen, File, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import { Badge } from './badge'
import { Button } from './button'
import { Card, CardContent } from './card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './collapsible'

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

interface TreeViewProps {
  node: FileNode
  onFileSelect?: (node: FileNode) => void
  level?: number
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'Critical':
      return <AlertTriangle className="h-4 w-4 text-red-500" />
    case 'Functional':
      return <AlertCircle className="h-4 w-4 text-orange-500" />
    case 'Minor':
      return <Info className="h-4 w-4 text-yellow-500" />
    default:
      return null
  }
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'Critical':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'Functional':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'Minor':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export function TreeView({ node, onFileSelect, level = 0 }: TreeViewProps) {
  const [isOpen, setIsOpen] = useState(level < 2) // Auto-expand first 2 levels
  const isDirectory = node.type === 'directory'
  const hasIssues = node.issue_count > 0

  const handleToggle = () => {
    if (isDirectory) {
      setIsOpen(!isOpen)
    } else if (onFileSelect) {
      onFileSelect(node)
    }
  }

  const paddingLeft = level * 20

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 py-1 px-2 hover:bg-gray-50 cursor-pointer rounded-sm ${
          hasIssues ? 'border-l-2 border-l-red-200' : ''
        }`}
        style={{ paddingLeft: `${paddingLeft + 8}px` }}
        onClick={handleToggle}
      >
        {/* Expand/Collapse Icon */}
        {isDirectory && (
          <Button variant="ghost" size="sm" className="h-4 w-4 p-0">
            {isOpen ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        )}
        
        {/* File/Folder Icon */}
        {isDirectory ? (
          isOpen ? (
            <FolderOpen className="h-4 w-4 text-blue-500" />
          ) : (
            <Folder className="h-4 w-4 text-blue-500" />
          )
        ) : (
          <File className="h-4 w-4 text-gray-500" />
        )}

        {/* Name */}
        <span className="text-sm font-medium text-gray-700 flex-1">
          {node.name}
        </span>

        {/* Issue Badges */}
        {hasIssues && (
          <div className="flex gap-1">
            {node.critical_issues > 0 && (
              <Badge variant="destructive" className="text-xs px-1 py-0">
                ⚠️ {node.critical_issues}
              </Badge>
            )}
            {node.functional_issues > 0 && (
              <Badge variant="secondary" className="text-xs px-1 py-0 bg-orange-100 text-orange-800">
                🐞 {node.functional_issues}
              </Badge>
            )}
            {node.minor_issues > 0 && (
              <Badge variant="outline" className="text-xs px-1 py-0 bg-yellow-100 text-yellow-800">
                🔍 {node.minor_issues}
              </Badge>
            )}
          </div>
        )}

        {/* Total Issue Count */}
        {hasIssues && (
          <Badge variant="outline" className="text-xs">
            {node.issue_count}
          </Badge>
        )}
      </div>

      {/* Children */}
      {isDirectory && isOpen && node.children && (
        <div>
          {node.children.map((child, index) => (
            <TreeView
              key={`${child.path}-${index}`}
              node={child}
              onFileSelect={onFileSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface IssueListProps {
  issues: IssueDetail[]
  title?: string
}

export function IssueList({ issues, title = "Issues" }: IssueListProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set())

  const toggleIssue = (index: number) => {
    const newExpanded = new Set(expandedIssues)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedIssues(newExpanded)
  }

  if (issues.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-gray-500 text-center">No issues found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">{title}</h3>
      {issues.map((issue, index) => (
        <Card key={index} className="border-l-4 border-l-gray-200">
          <CardContent className="p-4">
            <div
              className="flex items-start gap-3 cursor-pointer"
              onClick={() => toggleIssue(index)}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getSeverityIcon(issue.severity)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={`text-xs ${getSeverityColor(issue.severity)}`}>
                    {issue.severity}
                  </Badge>
                  <span className="text-sm font-medium text-gray-900">
                    {issue.type}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-2">
                  {issue.description}
                </p>
                
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{issue.file_path}</span>
                  {issue.line_number && (
                    <span>Line {issue.line_number}</span>
                  )}
                </div>
              </div>

              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                {expandedIssues.has(index) ? (
                  <ChevronDown className="h-3 w-3" />
                ) : (
                  <ChevronRight className="h-3 w-3" />
                )}
              </Button>
            </div>

            {/* Expanded Content */}
            {expandedIssues.has(index) && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                {issue.suggestion && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-green-700 mb-1">
                      💡 Suggestion:
                    </h4>
                    <p className="text-sm text-green-600 bg-green-50 p-2 rounded">
                      {issue.suggestion}
                    </p>
                  </div>
                )}
                
                {issue.context_lines && issue.context_lines.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      📄 Code Context:
                    </h4>
                    <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto">
                      <code>
                        {issue.context_lines.map((line, lineIndex) => (
                          <div
                            key={lineIndex}
                            className={`${
                              issue.line_number && 
                              lineIndex === Math.floor(issue.context_lines!.length / 2)
                                ? 'bg-yellow-100 font-medium'
                                : ''
                            }`}
                          >
                            {line}
                          </div>
                        ))}
                      </code>
                    </pre>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

