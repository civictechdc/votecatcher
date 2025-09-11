import { type NextRequest, NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const next = searchParams.get("next") ?? "/getting-started"

  const supabase = await createClient()

  // Get the code and state from the URL
  const code = searchParams.get("code")
  const state = searchParams.get("state")

  if (code && state) {
    // Exchange the code for a session
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (error) {
      console.error("Error exchanging code for session:", error.message)
      return NextResponse.redirect(`${origin}/auth?error=verification_failed`)
    }
  }

  return NextResponse.redirect(`${origin}${next}`)
}
