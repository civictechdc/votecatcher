"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Github, LogOut } from "lucide-react"
import { createClient } from "@/lib/supabase/client"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import type { User } from '@supabase/supabase-js';

interface NavbarProps {
  showAuthButtons?: boolean
  user?: User
}

export default function Navbar({ showAuthButtons = false, user }: NavbarProps) {
  const router = useRouter()
  const supabase = createClient()

  const handleSignOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) {
      console.error("Error signing out:", error.message)
    }
    router.push("/")
  }

  // Add this useEffect to detect mock user state
  useEffect(() => {
    if (showAuthButtons) {
      const mockUser = localStorage.getItem("mock_user")
      const isAuthenticated = localStorage.getItem("mock_authenticated")

      if (mockUser && isAuthenticated && !user) {
        // Update user prop would normally come from parent, but for demo purposes
        // we can show the user is logged in
      }
    }
  }, [showAuthButtons, user])

  return (
    <nav className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-blue-100">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-xl text-blue-900 flex items-center gap-2">
          VoteCatcher ✓
        </Link>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/civictechdc/Ballot-Initiative"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View Ballot Initiative on GitHub"
            className="inline-flex items-center justify-center p-2 text-slate-600 hover:text-slate-900"
          >
            <Github className="h-5 w-5" />
          </a>

          {showAuthButtons && user && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSignOut}
              className="border-red-200 text-red-700 hover:bg-red-50 bg-transparent"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          )}

          {showAuthButtons && !user && (
            <Link href="/auth">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
