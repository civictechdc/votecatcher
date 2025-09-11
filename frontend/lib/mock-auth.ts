export interface MockUser {
  id: string
  email: string
  created_at: string
}

export interface MockProfile {
  id: string
  email: string
  full_name?: string
  role?: string
  company?: string
  onboarded: boolean
  updated_at: string
}

export class MockAuth {
  static getCurrentUser(): MockUser | null {
    const user = localStorage.getItem("mock_user")
    const isAuthenticated = localStorage.getItem("mock_authenticated")

    if (user && isAuthenticated) {
      return JSON.parse(user)
    }
    return null
  }

  static async signUp(email: string, password: string): Promise<{ user: MockUser | null; error: string | null }> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Mock validation
    if (!email || !password) {
      return { user: null, error: "Email and password are required" }
    }

    if (password.length < 6) {
      return { user: null, error: "Password must be at least 6 characters" }
    }

    const mockUser: MockUser = {
      id: `user_${Date.now()}`,
      email,
      created_at: new Date().toISOString(),
    }

    localStorage.setItem("mock_user", JSON.stringify(mockUser))
    localStorage.setItem("mock_user_needs_verification", "true")

    return { user: mockUser, error: null }
  }

  static async signIn(email: string, password: string): Promise<{ user: MockUser | null; error: string | null }> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Mock validation
    if (!email || !password) {
      return { user: null, error: "Email and password are required" }
    }

    const mockUser: MockUser = {
      id: `user_${Date.now()}`,
      email,
      created_at: new Date().toISOString(),
    }

    localStorage.setItem("mock_user", JSON.stringify(mockUser))
    localStorage.setItem("mock_authenticated", "true")

    return { user: mockUser, error: null }
  }

  static async signOut(): Promise<void> {
    localStorage.removeItem("mock_user")
    localStorage.removeItem("mock_authenticated")
    // Keep profile data for demo purposes, but remove auth
  }

  static getProfile(email: string): MockProfile | null {
    const profileData = localStorage.getItem(`profile_${email}`)
    return profileData ? JSON.parse(profileData) : null
  }

  static async updateProfile(profile: Partial<MockProfile>): Promise<{ error: string | null }> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const user = this.getCurrentUser()
    if (!user) {
      return { error: "User not authenticated" }
    }

    const existingProfile = this.getProfile(user.email) || {
      id: user.id,
      email: user.email,
      onboarded: false,
      updated_at: new Date().toISOString(),
    }

    const updatedProfile = {
      ...existingProfile,
      ...profile,
      updated_at: new Date().toISOString(),
    }

    localStorage.setItem(`profile_${user.email}`, JSON.stringify(updatedProfile))
    return { error: null }
  }

  static isAuthenticated(): boolean {
    return !!(localStorage.getItem("mock_user") && localStorage.getItem("mock_authenticated"))
  }
}
