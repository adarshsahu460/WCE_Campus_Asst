import Link from 'next/link'
import { MessageCircle, Calendar, BookOpen, FileText } from 'lucide-react'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold text-slate-800 mb-4">
          Welcome to WCE Campus Assistant
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
          Your AI-powered companion for academic information, exam schedules,
          timetables, and more at Walchand College of Engineering.
        </p>
        <div className="mt-8">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 bg-wce-blue text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-800 transition-colors shadow-lg"
          >
            <MessageCircle className="w-6 h-6" />
            Start Chatting
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <FeatureCard
          icon={<MessageCircle className="w-8 h-8" />}
          title="AI Chat Assistant"
          description="Ask questions about academic regulations, syllabus, and college policies."
        />
        <FeatureCard
          icon={<Calendar className="w-8 h-8" />}
          title="Exam Reminders"
          description="Get notifications about upcoming exams and create study plans."
        />
        <FeatureCard
          icon={<BookOpen className="w-8 h-8" />}
          title="Timetable Viewer"
          description="Check your class schedule for any day of the week."
        />
        <FeatureCard
          icon={<FileText className="w-8 h-8" />}
          title="Document Search"
          description="Search through notices, syllabi, and academic documents."
        />
      </div>

      {/* Quick Actions */}
      <div className="mt-16">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 text-center">
          Quick Actions
        </h2>
        <div className="flex flex-wrap justify-center gap-4">
          <QuickActionButton href="/chat?q=What%20are%20today%27s%20classes">
            Today&apos;s Classes
          </QuickActionButton>
          <QuickActionButton href="/chat?q=Show%20upcoming%20exams">
            Upcoming Exams
          </QuickActionButton>
          <QuickActionButton href="/chat?q=What%20is%20the%20attendance%20requirement">
            Attendance Rules
          </QuickActionButton>
          <QuickActionButton href="/chat?q=Create%20a%20study%20plan">
            Study Planner
          </QuickActionButton>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow border border-slate-100">
      <div className="text-wce-blue mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-slate-800 mb-2">{title}</h3>
      <p className="text-slate-600 text-sm">{description}</p>
    </div>
  )
}

function QuickActionButton({
  href,
  children,
}: {
  href: string
  children: React.ReactNode
}) {
  return (
    <Link
      href={href}
      className="px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition-colors"
    >
      {children}
    </Link>
  )
}
