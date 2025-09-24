"use client"

import React from "react"
import { Vote, Brain, FileText } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import UploadCard from "./UploadCard"

interface SidebarProps {
  campaignName?: string;
  ocrProvider: string;
  ocrProviders: { value: string; label: string }[];
  handleOcrProviderChange: (value: string) => void;
  ocrPrompt: string;
  setOcrPrompt: (prompt: string) => void;
  uploadedPetitions: File[];
  removePetition: (index: number) => void;
  isConverting: boolean;
  uploadSuccess: boolean;
  uploadedFilesForOcr: File[];
  uploading: boolean;
  handleUploadPetitions: () => void;
  handleProcessWithOcr: () => void;
  isProcessing: boolean;
  ocrProgress: number;
  ocrError: string | null;
  ocrResults: OCRResult[];
  handlePetitionUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleFuzzyMatching?: () => void;
  isFuzzyMatching?: boolean;
}

interface OCRResult {
  name: string;
  address: string;
  ward: string;
  page_number: number;
  row_number: number;
}

const Sidebar = (props: SidebarProps) => {
  const {
    campaignName,
    ocrProvider,
    ocrProviders,
    handleOcrProviderChange,
    ocrPrompt,
    setOcrPrompt,
    uploadedPetitions,
    removePetition,
    isConverting,
    uploadSuccess,
    uploadedFilesForOcr,
    uploading,
    handleUploadPetitions,
    handleProcessWithOcr,
    isProcessing,
    ocrProgress,
    ocrError,
    ocrResults,
    handlePetitionUpload
  } = props;

  return (
    <div className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-72 bg-white border-r border-slate-200 shadow-lg overflow-y-auto">
      <div className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <Vote className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-blue-900">{campaignName || "Campaign Dashboard"}</h2>
        </div>
        <div className="space-y-6">
          {/* OCR Provider Selection */}
          <Card className="border-purple-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-purple-900 flex items-center gap-2">
                <Brain className="h-4 w-4" />
                OCR Provider (LLM)
              </CardTitle>
              <CardDescription className="text-xs">
                Select the AI model for optical character recognition
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                <Label htmlFor="ocr-provider" className="text-sm text-slate-700">
                  Provider
                </Label>
                <Select value={ocrProvider} onValueChange={handleOcrProviderChange}>
                  <SelectTrigger className="border-purple-200 focus:border-purple-500">
                    <SelectValue placeholder="Select OCR provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {ocrProviders.map((provider: { value: string; label: string }) => (
                      <SelectItem key={provider.value} value={provider.value}>
                        {provider.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* OCR Prompt */}
          <Card className="border-orange-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-orange-900 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                OCR Prompt
              </CardTitle>
              <CardDescription className="text-xs">Customize the prompt sent to the AI model</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                <Label htmlFor="ocr-prompt" className="text-sm text-slate-700">
                  Prompt Template
                </Label>
                <Textarea
                  id="ocr-prompt"
                  value={ocrPrompt}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setOcrPrompt(e.target.value)}
                  className="border-orange-200 focus:border-orange-500 min-h-[120px] text-xs"
                  placeholder="Enter your OCR prompt..."
                />
                <div className="text-xs text-orange-600 bg-orange-50 p-2 rounded">
                  <strong>Tip:</strong> This prompt will be sent to the AI model along with each petition image.
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Petition Upload */}
          <UploadCard
            uploadedPetitions={uploadedPetitions}
            removePetition={removePetition}
            isConverting={isConverting}
            uploadSuccess={uploadSuccess}
            uploadedFilesForOcr={uploadedFilesForOcr}
            uploading={uploading}
            handleUploadPetitions={handleUploadPetitions}
            handlePetitionUpload={handlePetitionUpload}
            handleProcessWithOcr={handleProcessWithOcr}
            isProcessing={isProcessing}
            ocrProgress={ocrProgress}
            ocrError={ocrError}
            ocrResults={ocrResults}
            ocrProvider={ocrProvider}
          />

          {/* Fuzzy Matching */}
          {props.handleFuzzyMatching && (
            <Card className="border-green-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-green-900 flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  Fuzzy Matching
                </CardTitle>
                <CardDescription className="text-xs">
                  Match registration data against voter records
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <button
                  onClick={props.handleFuzzyMatching}
                  disabled={props.isFuzzyMatching}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white font-medium py-2 px-4 rounded-md transition-colors"
                >
                  {props.isFuzzyMatching ? 'Running Fuzzy Matching...' : 'Run Fuzzy Matching'}
                </button>
                <div className="text-xs text-green-600 bg-green-50 p-2 rounded mt-2">
                  <strong>Note:</strong> This will replace existing matches for the current campaign.
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default Sidebar; 