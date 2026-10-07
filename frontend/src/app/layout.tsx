import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'OutreachAI - AI-Powered Cold Email Outreach',
  description: 'Discover companies and generate personalized cold emails with AI',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="bg-slate-900 text-white shadow-lg">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 px-4 py-4">
            <a href="/" className="text-2xl font-bold">
              🚀 OutreachAI
            </a>
            <nav className="flex items-center gap-4 text-sm font-medium text-slate-300">
              <a href="/" className="hover:text-white">Outreach</a>
              <a href="/linkedin" className="rounded-md bg-blue-600 px-3 py-1.5 text-white hover:bg-blue-500">LinkedIn jobs</a>
            </nav>
          </div>
        </header>

        <main className="min-h-screen bg-slate-50">
          <div className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </div>
        </main>

        <footer className="bg-slate-900 text-white mt-12 py-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm text-slate-400">
            <p>© 2024 OutreachAI. Powered by LangChain, LangGraph & AI.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
