import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Toaster } from 'react-hot-toast';
import Image from 'next/image';

const inter = Inter({ 
  subsets: ["latin"],
  display: 'swap',
  preload: true,
})

// Import CSS with proper preload handling
import "./globals.css"

export const metadata: Metadata = {
  title: "VoteCatcher ✓",
  description: "Open Source Campaign Infrastructure",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Toaster position="top-right" />
        {children}

        {/* Floating Sponsored by section */}
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-white/90 backdrop-blur-sm border border-slate-200 rounded-full px-3 py-2 shadow-lg">
          <span className="text-xs text-slate-500 font-medium">Sponsored by</span>
          <div className="w-6 h-6 rounded-full overflow-hidden border border-slate-200">
            <Image src="/sponsor-logo.jpg" alt="Sponsor logo" width={24} height={24} className="w-full h-full object-cover" />
          </div>
        </div>
      </body>
    </html>
  )
}
