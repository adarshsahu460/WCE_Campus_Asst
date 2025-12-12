'use client'

import { Calendar, Clock, MapPin, AlertCircle } from 'lucide-react'

interface CardExamReminderProps {
  subject: string
  date: string
  daysUntil: number
  venue?: string
  time?: string
}

export default function CardExamReminder({
  subject,
  date,
  daysUntil,
  venue,
  time,
}: CardExamReminderProps) {
  const getUrgencyColor = () => {
    if (daysUntil <= 2) return 'border-red-500 bg-red-50'
    if (daysUntil <= 5) return 'border-orange-500 bg-orange-50'
    return 'border-blue-500 bg-blue-50'
  }

  const getUrgencyText = () => {
    if (daysUntil === 0) return 'Today!'
    if (daysUntil === 1) return 'Tomorrow!'
    return `${daysUntil} days left`
  }

  const getUrgencyBadgeColor = () => {
    if (daysUntil <= 2) return 'bg-red-500 text-white'
    if (daysUntil <= 5) return 'bg-orange-500 text-white'
    return 'bg-blue-500 text-white'
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className={`border-l-4 rounded-lg p-3 ${getUrgencyColor()}`}>
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold text-slate-800 text-sm">{subject}</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full ${getUrgencyBadgeColor()}`}>
          {getUrgencyText()}
        </span>
      </div>
      
      <div className="space-y-1 text-xs text-slate-600">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>{formatDate(date)}</span>
        </div>
        
        {time && (
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{time}</span>
          </div>
        )}
        
        {venue && (
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            <span>{venue}</span>
          </div>
        )}
      </div>
      
      {daysUntil <= 2 && (
        <div className="mt-2 flex items-center gap-1 text-red-600 text-xs">
          <AlertCircle className="w-3 h-3" />
          <span>Prepare now!</span>
        </div>
      )}
    </div>
  )
}
