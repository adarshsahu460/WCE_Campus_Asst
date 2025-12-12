'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Bot, User, FileText, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Message, Source } from '../chat/page'

interface ChatUIProps {
  messages: Message[]
  isLoading: boolean
  onSendMessage: (message: string) => void
  onUploadClick: () => void
}

export default function ChatUI({
  messages,
  isLoading,
  onSendMessage,
  onUploadClick,
}: ChatUIProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <WelcomeMessage onExampleClick={onSendMessage} />
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <button
            type="button"
            onClick={onUploadClick}
            className="p-3 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Upload document"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about timetables, exams, regulations..."
            className="flex-1 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-wce-blue text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`chat-message flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-wce-blue text-white' : 'bg-slate-200 text-slate-600'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div
        className={`max-w-[80%] ${
          isUser ? 'bg-wce-blue text-white' : 'bg-white border border-slate-200'
        } rounded-2xl px-4 py-3 shadow-sm`}
      >
        <div className={`prose prose-sm ${isUser ? 'prose-invert' : ''} max-w-none`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200">
            <p className="text-xs font-semibold text-slate-500 mb-2">Sources:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <SourceBadge key={index} source={source} />
              ))}
            </div>
          </div>
        )}

        {/* Tool Calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200">
            <p className="text-xs font-semibold text-slate-500 mb-2">Tools Used:</p>
            <div className="flex flex-wrap gap-2">
              {message.toolCalls.map((tool, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                >
                  🔧 {tool.tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function SourceBadge({ source }: { source: Source }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs">
      <FileText className="w-3 h-3" />
      {source.filename}
      <span className="text-slate-400">({(source.score * 100).toFixed(0)}%)</span>
    </span>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
        <Bot className="w-4 h-4 text-slate-600" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-sm">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  )
}

function WelcomeMessage({ onExampleClick }: { onExampleClick: (msg: string) => void }) {
  const examples = [
    "What are today's classes?",
    "Show my upcoming exams",
    "What is the minimum attendance requirement?",
    "Create a study plan for Data Structures exam",
    "Show recent notices",
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 bg-wce-blue rounded-full flex items-center justify-center mb-4">
        <Bot className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-slate-800 mb-2">
        Welcome to WCE Campus Assistant
      </h2>
      <p className="text-slate-600 mb-8 max-w-md">
        I can help you with academic information, exam schedules, timetables,
        and more. Try asking me something!
      </p>
      <div className="grid gap-2 max-w-lg">
        {examples.map((example, index) => (
          <button
            key={index}
            onClick={() => onExampleClick(example)}
            className="text-left px-4 py-3 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-colors text-sm text-slate-600"
          >
            <span className="text-wce-blue">💬</span> {example}
          </button>
        ))}
      </div>
    </div>
  )
}
