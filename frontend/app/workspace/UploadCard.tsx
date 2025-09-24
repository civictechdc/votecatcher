"use client"

import React from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Upload, FileText, X, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

interface UploadCardProps {
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
  ocrResults: unknown[];
  ocrProvider: string;
  handlePetitionUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const UploadCard = (props: UploadCardProps) => {
  const {
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
    ocrProvider
  } = props;

  return (
    <Card className="border-blue-200">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-blue-900 flex items-center gap-2">
          <Upload className="h-4 w-4" />
          Upload Petitions
        </CardTitle>
        <CardDescription className="text-xs">Upload petition images for OCR processing</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="border-2 border-dashed border-blue-200 rounded-lg p-4 text-center hover:border-blue-300 transition-colors">
            <input
              type="file"
              id="petition-upload"
              className="hidden"
              accept="image/*,.pdf"
              multiple
              onChange={(e) => {
                console.log("UploadCard input onChange fired", e.target.files);
                props.handlePetitionUpload(e);
              }}
            />
            <label htmlFor="petition-upload" className="cursor-pointer">
              <Upload className="h-8 w-8 text-blue-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-700 mb-1">Upload Petition Images</p>
              <p className="text-xs text-slate-500">PNG, JPG, PDF files</p>
            </label>
          </div>

          {uploadedPetitions.length > 0 && (
            <div className="space-y-2 max-h-32 overflow-y-auto">
              <Label className="text-xs text-slate-500">Uploaded Files ({uploadedPetitions.length})</Label>
              {uploadedPetitions.map((file: File, index: number) => (
                <div key={index} className="flex items-center justify-between bg-blue-50 p-2 rounded text-xs">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <FileText className="h-3 w-3 text-blue-600 flex-shrink-0" />
                    <span className="truncate text-blue-800">{file.name}</span>
                  </div>
                  <button
                    onClick={() => removePetition(index)}
                    className="text-red-500 hover:text-red-700 flex-shrink-0 ml-2"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {isConverting && (
            <div className="flex items-center gap-2 text-blue-600 text-sm py-2">
              <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              Converting PDF to images...
            </div>
          )}
          {uploadSuccess && (
            <div className="flex items-center gap-2 text-green-600 text-sm py-2">
              <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              Petitions uploaded successfully!
            </div>
          )}
          {uploadedFilesForOcr.length > 0 && (
            <div className="flex items-center gap-2 text-blue-600 text-sm py-2 bg-blue-50 p-2 rounded">
              <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              {uploadedFilesForOcr.length} file(s) ready for OCR processing
            </div>
          )}
          {uploading && (
            <div className="flex items-center gap-2 text-blue-600 text-sm py-2">
              <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              Uploading petitions to database...
            </div>
          )}

          <Button
            className="w-full bg-blue-600 hover:bg-blue-700 text-sm"
            disabled={uploadedPetitions.length === 0}
            onClick={handleUploadPetitions}
          >
            Upload Petitions
          </Button>

          {/* Process with OCR Button */}
          <Button
            className="w-full bg-green-600 hover:bg-green-700 text-sm"
            disabled={uploadedFilesForOcr.length === 0 || isProcessing || !ocrProvider}
            onClick={handleProcessWithOcr}
          >
            {isProcessing ? (
              <>
                <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
                Processing OCR... ({Math.round(ocrProgress)}%)
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Process with OCR
              </>
            )}
          </Button>

          {/* OCR Progress and Error Messages */}
          {isProcessing && ocrProgress > 0 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${ocrProgress}%` }}
              ></div>
            </div>
          )}

          {ocrError && (
            <div className="flex items-center gap-2 text-red-600 text-sm py-2 bg-red-50 p-2 rounded">
              <svg className="h-4 w-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              {ocrError}
            </div>
          )}

          {ocrResults.length > 0 && (
            <div className="flex items-center gap-2 text-green-600 text-sm py-2 bg-green-50 p-2 rounded">
              <svg className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              OCR processing complete! {ocrResults.length} entries processed.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default UploadCard; 