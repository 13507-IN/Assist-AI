import './globals.css';
import { ReactNode } from 'react';
import Link from 'next/link';
import StatusBanner from '@/components/StatusBanner';
import { ToastProvider } from '@/components/ToastProvider';

export const metadata = {
  title: 'OutreachAI - AI-Powered Cold Email Outreach',
  description: 'Discover companies and generate personalized cold emails with AI',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>
          <header className="bg-slate-900 text-white shadow-lg">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 px-4 py-4">
              <Link href="/" className="text-2xl font-bold">
                🚀 OutreachAI
              </Link>
              <nav className="flex items-center gap-4 text-sm font-medium text-slate-300">
                <Link href="/" className="hover:text-white">Outreach</Link>
                <Link href="/results" className="hover:text-white">Results</Link>
                <Link href="/activity" className="hover:text-white">Activity</Link>
                <Link href="/linkedin" className="rounded-md bg-blue-600 px-3 py-1.5 text-white hover:bg-blue-500">LinkedIn jobs</Link>
              </nav>
            </div>
          </header>

          <StatusBanner />

          <main className="min-h-screen bg-slate-50">
            <div className="max-w-7xl mx-auto px-4 py-8">
              {children}
            </div>
          </main>

          <footer className="bg-slate-900 text-white mt-12 py-8">
            <div className="max-w-7xl mx-auto px-4 text-center text-sm text-slate-400">
              <p>© 2026 OutreachAI. Powered by Gemini, MongoDB & Gmail.</p>
            </div>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}
