"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ArrowRight, ArrowLeft, Upload } from "lucide-react"
import { createClient } from "@/lib/supabase/client"
import Navbar from "@/components/navbar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import toast from 'react-hot-toast';
import type { User } from '@supabase/supabase-js';

const questions = [
  {
    id: 1,
    title: "Choose your AI provider",
    description: "Select which AI service you&apos;ll use for signature validation and enter your API key",
    placeholder: "Select an AI provider",
    field: "api_provider",
    type: "select_with_input",
    options: [
      { value: "OPENAI_API_KEY", label: "OpenAI (GPT-4)", placeholder: "Enter your OpenAI API key (sk-...)" },
      { value: "GEMINI_API_KEY", label: "Google Gemini", placeholder: "Enter your Gemini API key" },
      { value: "MISTRAL_API_KEY", label: "Mistral AI", placeholder: "Enter your Mistral API key" },
    ],
  },
  {
    id: 2,
    title: "Campaign Details",
    description: "Enter your campaign name and select the election year",
    placeholder: "e.g., Smith for Mayor, Proposition 15, Save Our Parks",
    field: "campaign_name",
    type: "campaign_details",
  },
  {
    id: 3,
    title: "Upload Registration Data",
    description: "Upload voter registration data from your local machine for signature validation",
    field: "registration_data",
    type: "file_upload",
  },
]

export default function GettingStartedPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const router = useRouter()
  const supabase = createClient()
  const [campaignNameError, setCampaignNameError] = useState<string | null>(null);

  useEffect(() => {
    // Check for authenticated user
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session?.user) {
        router.push("/auth")
      } else {
        setUser(session.user)
      }
    }

    checkAuth()
  }, [router, supabase.auth])

  const currentQuestion = questions[currentStep]
  const progress = ((currentStep + 1) / questions.length) * 100

  // Generate years for dropdown
  const generateYears = () => {
    const currentYear = new Date().getFullYear()
    const years = []
    for (let i = currentYear + 2; i >= currentYear - 2; i--) {
      years.push({ value: i.toString(), label: i.toString() })
    }
    return years
  }

  const handleNext = async () => {
    // If we're on the campaign details step (step 1), validate campaign name length
    if (currentStep === 1 && currentQuestion.type === "campaign_details") {
      if (!answers.campaign_name || answers.campaign_name.length < 3) {
        setCampaignNameError("Campaign name must be at least 3 characters long.");
        return;
      } else {
        setCampaignNameError(null);
      }
    }
    // If we're on the API key step (step 0), insert the API key immediately
    if (currentStep === 0 && currentQuestion.type === "select_with_input") {
      if (answers.api_provider && answers[`${currentQuestion.field}_api_key`]) {
        const provider = answers.api_provider
        const apiKey = answers[`${currentQuestion.field}_api_key`]

        console.log('Inserting API key immediately on Next click...')
        console.log('Provider:', provider)
        console.log('API Key length:', apiKey?.length)

        if (provider && apiKey) {
          setLoading(true)
          try {
            // Call the new API route to store the API key securely
            const response = await fetch('/api/store-api-key', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ provider, apiKey }),
            });
            const result = await response.json();
            if (!response.ok) {
              throw new Error(result.error || 'Failed to store API key');
            }
            console.log('API key inserted successfully on Next click')
            console.log('Inserted data:', result)
          } catch (error) {
            console.error('Error during API key insertion:', error)
          } finally {
            setLoading(false)
          }
        }
      }
    }

    // If we're on the campaign details step (step 1), insert the campaign immediately
    if (currentStep === 1 && currentQuestion.type === "campaign_details") {
      if (answers.campaign_name && answers.campaign_year) {
        const campaignName = answers.campaign_name
        const campaignYear = parseInt(answers.campaign_year)
        const campaignDescription = answers.campaign_description || null

        console.log('Inserting campaign immediately on Next click...')
        console.log('Campaign Name:', campaignName)
        console.log('Campaign Year:', campaignYear)
        console.log('Campaign Description:', campaignDescription)

        if (campaignName && campaignYear) {
          setLoading(true)
          try {
            // First, deactivate any existing active campaigns for this user
            const { error: deactivateError } = await supabase
              .from('campaign')
              .update({ status: 'inactive' })
              .eq('user_id', user?.id)
              .eq('status', 'active');

            if (deactivateError) {
              console.error('Error deactivating existing campaigns:', deactivateError);
            } else {
              console.log('Deactivated existing active campaigns');
            }

            // Then create the new active campaign
            const { data, error: campaignError } = await supabase
              .from('campaign')
              .insert({
                user_id: user?.id,
                name: campaignName,
                description: campaignDescription,
                year: campaignYear,
                status: 'active',
                is_active: true
              })
              .select('id')
              .single();

            if (campaignError) {
              console.error('Error inserting campaign:', campaignError)
              console.error('Error details:', campaignError.message, campaignError.details, campaignError.hint)
            } else {
              console.log('Campaign inserted successfully on Next click')
              console.log('Inserted data:', data)
              // Save campaign_id in answers
              setAnswers((prev) => ({ ...prev, campaign_id: data.id }));
            }
          } catch (error) {
            console.error('Error during campaign insertion:', error)
          } finally {
            setLoading(false)
          }
        }
      }
    }

    // Proceed to next step
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleComplete()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async () => {
    if (!user) return

    setLoading(true)

    try {
      // Mock profile update (API key insertion is now handled in handleNext)
      await new Promise((resolve) => setTimeout(resolve, 1500)) // Simulate API delay

      const profileData = {
        id: user.id,
        email: user.email,
        ...answers,
        registration_file_name: uploadedFile?.name || null,
        registration_file_size: uploadedFile?.size || null,
        onboarded: true,
        updated_at: new Date().toISOString(),
      }

      // Store mock profile data
      localStorage.setItem(`profile_${user.email}`, JSON.stringify(profileData))

      // Store uploaded file info (in real app, this would be uploaded to server)
      if (uploadedFile) {
        // Upload to Supabase Storage and trigger Edge Function
        const userId = user?.id;
        const campaignId = answers.campaign_id || "no-campaign-id";
        const filePath = `${userId}/${campaignId}/${uploadedFile.name}`;
        const { data, error } = await supabase.storage
          .from("voter-files")
          .upload(filePath, uploadedFile, { upsert: true });
        if (error) {
          console.error("Upload error:", error.message);
          toast.error("Failed to upload file: " + error.message);
        } else {
          console.log("File uploaded:", data);
          try {
            // Get the user's access token
            const { data: { session } } = await supabase.auth.getSession();
            const accessToken = session?.access_token;
            // Get the Supabase URL to construct the function URL
            const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
            const functionUrl = `${supabaseUrl}/functions/v1/process-voter-file`;
            
            const response = await fetch(
              functionUrl,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  ...(accessToken ? { "Authorization": `Bearer ${accessToken}` } : {}),
                },
                body: JSON.stringify({
                  filePath,
                  campaign_id: campaignId,
                  user_id: userId,
                }),
              }
            );
            const result = await response.json();
            if (!response.ok) {
              toast.error("Processing error: " + (result.error || response.statusText));
            } else {
              toast.success("File processing started! Records processed: " + result.records_processed);
            }
          } catch (err) {
            console.error("Error calling process-voter-file function:", err);
            const message = err instanceof Error ? err.message : String(err);
            toast.error("Error calling process-voter-file function: " + message);
          }
        }
      }

      setLoading(false)
      router.push("/workspace")
    } catch (error) {
      console.error('Error during completion:', error)
      setLoading(false)
    }
  }

  const updateAnswer = (value: string, field?: string) => {
    const targetField = field || currentQuestion.field
    setAnswers((prev) => ({
      ...prev,
      [targetField]: value,
    }))
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadedFile(file);
    updateAnswer(file.name, "registration_data");
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
    
    const files = event.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      // Check if file type is allowed
      const allowedTypes = ['.csv', '.xlsx', '.xls', '.json']
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
      
      if (allowedTypes.includes(fileExtension)) {
        setUploadedFile(file)
        updateAnswer(file.name, "registration_data")
      } else {
        console.error('Invalid file type. Please upload CSV, Excel, or JSON files.')
        // You could add a toast notification here
      }
    }
  }

  const canProceed = () => {
    if (currentQuestion.type === "select_with_input") {
      return (
        answers[currentQuestion.field]?.trim().length > 0 &&
        answers[`${currentQuestion.field}_api_key`]?.trim().length > 0
      )
    } else if (currentQuestion.type === "campaign_details") {
      return answers["campaign_name"]?.trim().length > 0 && answers["campaign_year"]?.trim().length > 0
    } else if (currentQuestion.type === "file_upload") {
      return uploadedFile !== null
    }
    return answers[currentQuestion?.field]?.trim().length > 0
  }

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar showAuthButtons user={user} />
      <div className="container mx-auto px-4 py-16 flex items-center justify-center">
        <Card className="w-full max-w-lg border-blue-200">
          <CardHeader>
            <div className="space-y-4">
              <Progress value={progress} className="w-full" />
              <div className="text-center">
                <CardTitle className="text-2xl text-blue-900">{currentQuestion.title}</CardTitle>
                <CardDescription className="mt-2 text-slate-600">{currentQuestion.description}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="answer" className="text-slate-700">
                Step {currentStep + 1} of {questions.length}
              </Label>

              {currentQuestion.type === "select_with_input" ? (
                <div className="space-y-4">
                  <Select value={answers[currentQuestion.field] || ""} onValueChange={(value) => updateAnswer(value)}>
                    <SelectTrigger className="border-blue-200 focus:border-blue-500">
                      <SelectValue placeholder={currentQuestion.placeholder} />
                    </SelectTrigger>
                    <SelectContent>
                      {currentQuestion.options?.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {answers[currentQuestion.field] && (
                    <div className="space-y-2">
                      <Label htmlFor="api-key" className="text-slate-700">
                        API Key
                      </Label>
                      <Input
                        id="api-key"
                        type="password"
                        placeholder={
                          currentQuestion.options?.find((opt) => opt.value === answers[currentQuestion.field])
                            ?.placeholder || "Enter your API key"
                        }
                        value={answers[`${currentQuestion.field}_api_key`] || ""}
                        onChange={(e) => updateAnswer(e.target.value, `${currentQuestion.field}_api_key`)}
                      />
                    </div>
                  )}
                </div>
              ) : currentQuestion.type === "campaign_details" ? (
                <div className="space-y-4">
                  <Input
                    id="campaign-name"
                    placeholder={currentQuestion.placeholder}
                    value={answers.campaign_name || ""}
                    onChange={(e) => updateAnswer(e.target.value, "campaign_name")}
                  />
                  {campaignNameError && (
                    <div className="text-red-600 text-sm">{campaignNameError}</div>
                  )}
                  <Select
                    value={answers.campaign_year || ""}
                    onValueChange={(value) => updateAnswer(value, "campaign_year")}
                  >
                    <SelectTrigger className="border-blue-200 focus:border-blue-500">
                      <SelectValue placeholder="Select an election year" />
                    </SelectTrigger>
                    <SelectContent>
                      {generateYears().map((year) => (
                        <SelectItem key={year.value} value={year.value}>
                          {year.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Textarea
                    id="campaign-description"
                    placeholder="Describe your campaign (optional)"
                    value={answers.campaign_description || ""}
                    onChange={(e) => updateAnswer(e.target.value, "campaign_description")}
                  />
                </div>
              ) : currentQuestion.type === "file_upload" ? (
                <div className="space-y-4">
                  <input
                    type="file"
                    id="registration-data"
                    accept=".csv, .xlsx, .xls, .json"
                    onChange={handleFileUpload}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    className="hidden"
                  />
                  <Button
                    onClick={() => document.getElementById("registration-data")?.click()}
                    className="w-full"
                    variant="outline"
                    disabled={loading}
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {loading ? "Uploading..." : "Choose File or Drop Here"}
                  </Button>
                  {uploadedFile && (
                    <div className="flex items-center justify-between text-sm text-slate-600">
                      <span>{uploadedFile.name}</span>
                      <span>{uploadedFile.size} bytes</span>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
            <div className="flex justify-between">
              <Button variant="outline" onClick={handleBack} disabled={currentStep === 0}>
                <ArrowLeft className="mr-2 h-4 w-4" /> Back
              </Button>
              <Button onClick={handleNext} disabled={!canProceed() || loading}>
                {currentStep === questions.length - 1 ? "Complete" : "Next"}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}