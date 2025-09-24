"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Users, Shield, Flag } from "lucide-react"
import { useEffect, useState } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import Navbar from "@/components/navbar";

export default function LandingPage() {
  const [user, setUser] = useState<User>()
  const supabase = createClient()
  
  useEffect(() => {
    const getAuthUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUser(session.user);
      }
    }
    getAuthUser()
  }, [])

  const homeLink = user ? "/workspace" : "/auth"

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50">
      <Navbar showAuthButtons user={user} />
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-6">
            <h1 className="text-5xl font-bold text-slate-900">VoteCatcher ✓</h1>
          </div>
          <p className="text-xl text-slate-700 mb-4 max-w-3xl mx-auto font-medium">
            Open Source Campaign Infrastructure
          </p>
          <p className="text-lg text-slate-600 mb-8 max-w-2xl mx-auto">
            Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of
            grassroots campaigns.
            <span className="text-blue-700 font-semibold"> Democracy should be accessible to everyone.</span>
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link href={homeLink}>
              <Button size="lg" className="text-lg px-8 py-3 bg-blue-600 hover:bg-blue-700">
                Start Your Campaign <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="text-lg px-8 py-3 border-red-200 text-red-700 hover:bg-red-50 bg-transparent"
            >
              Learn More
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center p-6 bg-white rounded-lg shadow-sm border border-blue-100">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-blue-900">Signature Validation</h3>
              <p className="text-slate-600">
                High-accuracy signature triaging using multimodal LLMs integrated with voter files.
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-lg shadow-sm border border-red-100">
              <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="h-8 w-8 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-red-900">Grassroots Focused</h3>
              <p className="text-slate-600">
                Built for community organizers and campaigns that need powerful tools without the high costs.
              </p>
            </div>

            <div className="text-center p-6 bg-white rounded-lg shadow-sm border border-slate-200">
              <div className="bg-slate-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Flag className="h-8 w-8 text-slate-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-slate-900">Open Source</h3>
              <p className="text-slate-600">
                Transparent, community-driven technology that strengthens democratic participation.
              </p>
            </div>
          </div>

          <div className="mt-16 p-8 bg-gradient-to-r from-blue-600 to-red-600 rounded-lg text-white">
            <h2 className="text-2xl font-bold mb-4">🗳️ Why This Matters</h2>
            <p className="text-lg opacity-90 max-w-3xl mx-auto">
              Running a grassroots campaign shouldn&apos;t require expensive software or technical expertise. We believe
              technology should make democratic participation easier, not harder. VoteCatcher puts campaign
              infrastructure in the hands of the people.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
