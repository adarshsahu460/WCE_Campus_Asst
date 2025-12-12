'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatUI from '../components/ChatUI'
import FileUpload from '../components/FileUpload'
import CardExamReminder from '../components/CardExamReminder'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  toolCalls?: ToolCall[]
  timestamp: Date
}

export interface Source {
  index: number
  source: string
  category: string
  score: number
  filename: string
}

export interface ToolCall {
  tool: string
  params: Record<string, unknown>
  result: unknown
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [upcomingExams, setUpcomingExams] = useState<unknown[]>([])
  const searchParams = useSearchParams()

  // Handle initial query from URL
  useEffect(() => {
    const initialQuery = searchParams.get('q')
    if (initialQuery && messages.length === 0) {
      handleSendMessage(initialQuery)
    }
  }, [searchParams])

  // Fetch upcoming exams on mount
  useEffect(() => {
    fetchUpcomingExams()
  }, [])

  const fetchUpcomingExams = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'Show upcoming exams',
            use_rag: false,
            use_tools: true,
          }),
        }
      )
      const data = await response.json()
      if (data.tool_calls?.[0]?.result?.exams) {
        setUpcomingExams(data.tool_calls[0].result.exams)
      }
    } catch (error) {
      console.error('Failed to fetch exams:', error)
    }
  }

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content,
            conversation_history: messages.map((m) => ({
              role: m.role,
              content: m.content,
            })),
            use_rag: true,
            use_tools: true,
          }),
        }
      )

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'Sorry, I could not process your request.',
        sources: data.sources,
        toolCalls: data.tool_calls,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          'Sorry, there was an error connecting to the server. Please make sure the backend is running.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file: File, category: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', category)
    formData.append('index_immediately', 'true')

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/upload/`,
        {
          method: 'POST',
          body: formData,
        }
      )

      const data = await response.json()
      
      if (data.indexed) {
        const systemMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `✅ File "${data.filename}" uploaded and indexed successfully! (${data.chunks_indexed} chunks)`,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, systemMessage])
      }

      setShowUpload(false)
    } catch (error) {
      console.error('Upload error:', error)
    }
  }

  return (
    <div className="flex h-[calc(100vh-140px)]">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <ChatUI
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          onUploadClick={() => setShowUpload(true)}
        />
      </div>

      {/* Sidebar */}
      <div className="hidden lg:block w-80 border-l bg-white p-4 overflow-y-auto">
        <h3 className="font-semibold text-slate-700 mb-4">Upcoming Exams</h3>
        {upcomingExams.length > 0 ? (
          <div className="space-y-3">
            {upcomingExams.slice(0, 5).map((exam: any, index: number) => (
              <CardExamReminder
                key={index}
                subject={exam.subject}
                date={exam.date || exam.parsed_date}
                daysUntil={exam.days_until}
                venue={exam.venue}
              />
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No upcoming exams found.</p>
        )}

        <div className="mt-8">
          <h3 className="font-semibold text-slate-700 mb-4">Quick Questions</h3>
          <div className="space-y-2">
            {[
              "What's my timetable for today?",
              "Create a study plan for exams",
              "What is the attendance policy?",
              "Show available notices",
            ].map((question, index) => (
              <button
                key={index}
                onClick={() => handleSendMessage(question)}
                className="w-full text-left text-sm p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <FileUpload
          onUpload={handleFileUpload}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  )
}
