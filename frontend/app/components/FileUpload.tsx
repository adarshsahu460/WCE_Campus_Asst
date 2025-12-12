'use client'

import { useState, useRef } from 'react'
import { X, Upload, FileText } from 'lucide-react'

interface FileUploadProps {
  onUpload: (file: File, category: string) => void
  onClose: () => void
}

const CATEGORIES = [
  { id: 'timetable', label: 'Timetable', description: 'Class schedules' },
  { id: 'exam', label: 'Exam Schedule', description: 'Exam timetables' },
  { id: 'notice', label: 'Notice', description: 'Department notices' },
  { id: 'syllabus', label: 'Syllabus', description: 'Course syllabi' },
  { id: 'regulation', label: 'Regulation', description: 'Academic rules' },
  { id: 'general', label: 'General', description: 'Other documents' },
]

export default function FileUpload({ onUpload, onClose }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [category, setCategory] = useState('general')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file && isValidFile(file)) {
      setSelectedFile(file)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && isValidFile(file)) {
      setSelectedFile(file)
    }
  }

  const isValidFile = (file: File): boolean => {
    const validExtensions = ['.pdf', '.csv', '.txt', '.md']
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return validExtensions.includes(extension)
  }

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile, category)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-slate-800">Upload Document</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.csv,.txt,.md"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {selectedFile ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-10 h-10 text-blue-500" />
                <div className="text-left">
                  <p className="font-medium text-slate-800">{selectedFile.name}</p>
                  <p className="text-sm text-slate-500">{formatFileSize(selectedFile.size)}</p>
                </div>
              </div>
            ) : (
              <>
                <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600 mb-2">
                  Drag and drop your file here, or click to browse
                </p>
                <p className="text-sm text-slate-400">
                  Supports PDF, CSV, TXT, MD files
                </p>
              </>
            )}
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Document Category
            </label>
            <div className="grid grid-cols-2 gap-2">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setCategory(cat.id)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    category === cat.id
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <p className="font-medium text-sm">{cat.label}</p>
                  <p className="text-xs text-slate-500">{cat.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t bg-slate-50 rounded-b-xl">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedFile}
            className="flex-1 px-4 py-2 bg-wce-blue text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Upload & Index
          </button>
        </div>
      </div>
    </div>
  )
}
