import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'WCE Campus Assistant',
  description: 'AI-powered campus assistant for Walchand College of Engineering',
  keywords: ['WCE', 'Walchand', 'Campus', 'Assistant', 'AI', 'Chatbot'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-wce-blue text-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-wce-gold rounded-full flex items-center justify-center font-bold text-wce-blue">
                  WCE
                </div>
                <div>
                  <h1 className="text-xl font-bold">WCE Campus Assistant</h1>
                  <p className="text-xs text-blue-200">Walchand College of Engineering</p>
                </div>
              </div>
              <nav className="hidden md:flex gap-6">
                <a href="/" className="hover:text-wce-gold transition-colors">Home</a>
                <a href="/chat" className="hover:text-wce-gold transition-colors">Chat</a>
              </nav>
            </div>
          </header>
          
          {/* Main Content */}
          <main className="flex-1">
            {children}
          </main>
          
          {/* Footer */}
          <footer className="bg-slate-100 border-t py-4">
            <div className="max-w-7xl mx-auto px-4 text-center text-sm text-slate-600">
              <p>© 2024 WCE Campus Assistant. Built with ❤️ for WCE students.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
