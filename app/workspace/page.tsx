"use client"

import React from "react"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Database } from "lucide-react"
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf";
// The worker file is now served from the public directory
pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";
import { 
  encodeImageToBase64, 
  insertOcrResultsToSupabase 
} from "./ocrProcessing";
import { callOcrApi } from "./ocrApi";
import Sidebar from "./Sidebar";
import DataTable from "./DataTable";
import toast from 'react-hot-toast';
import type { User } from '@supabase/supabase-js';
import { createClient } from "@/lib/supabase/client";
import Navbar from "@/components/navbar";
import type { OCRResult } from "./ocrApi";
import type { RegistrationRecord, MatchRecord } from "./DataTable";

export default function WorkspacePage() {
  const [user, setUser] = useState<User | null>(null)
  const [campaignName, setCampaignName] = useState<string | null>(null)
  const [campaignId, setCampaignId] = useState<string | null>(null)
  const [ocrProvider, setOcrProvider] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()
  const [ocrPrompt, setOcrPrompt] = useState<string>(
    "Using the written text in the image, create a JSON array where each object consists of keys 'name', 'address', 'date', and 'ward'. For the 'date' field, always use the format YYYY-MM-DD (e.g., 2024-01-15). Fill in the values of each object with the correct entries for each key. Write all the values of the object in full. Only output the JSON array. No other intro text is necessary.",
  )
  const [uploadedPetitions, setUploadedPetitions] = useState<File[]>([]);
  const [uploadedFilesForOcr, setUploadedFilesForOcr] = useState<File[]>([]);
  const [ocrProviders, setOcrProviders] = useState<{ value: string; label: string }[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [config, setConfig] = useState<{ BASE_THRESHOLD: number; TOP_CROP: number; BOTTOM_CROP: number } | null>(null);
  
  // OCR processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [ocrResults, setOcrResults] = useState<OCRResult[]>([]);
  const [ocrError, setOcrError] = useState<string | null>(null);
  
  // Registration data state
  const [registrationData, setRegistrationData] = useState<RegistrationRecord[]>([]);
  const [dataLoading, setDataLoading] = useState(false);

  const [mappedMatches, setMappedMatches] = useState<MatchRecord[]>([]);
  const [selectedMatchRanks, setSelectedMatchRanks] = useState<{ [registrationId: string]: number }>({});
  const [isFuzzyMatching, setIsFuzzyMatching] = useState(false);

  // Move fetchRegistrationData above useEffect
  const fetchRegistrationData = useCallback(async () => {
    if (!campaignId || !user) return;
    setDataLoading(true);
    try {
      const { data, error } = await supabase
        .from('registration_data')
        .select('*')
        .eq('campaign_id', campaignId)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });
      if (error) {
        console.error('Error fetching registration data:', error);
        setRegistrationData([]);
      } else {
        setRegistrationData(data || []);
      }
    } catch (error) {
      console.error('Error fetching registration data:', error);
      setRegistrationData([]);
    } finally {
      setDataLoading(false);
    }
  }, [campaignId, user, supabase]);

  useEffect(() => {
    const checkAuthAndFetchCampaignAndOcr = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.user) {
        router.push("/auth");
        return;
      }
      setUser(session.user);
      // Fetch the most recent campaign for this user (regardless of status)
      const { data: campaigns, error: campaignError } = await supabase
        .from('campaign')
        .select('id, name, status, created_at')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false });
      
      let campaign: { id: string; name: string; status: string; created_at: string } | null = null;
      if (!campaignError && campaigns && campaigns.length > 0) {
        // If there are multiple campaigns, prefer the most recent active one, otherwise take the most recent
        const activeCampaign = campaigns.find((c: { status: string }) => c.status === 'active');
        campaign = activeCampaign || campaigns[0];
      }
      if (!campaignError && campaign) {
        console.log("Found campaign:", campaign);
        console.log("All campaigns for user:", campaigns);
        setCampaignName(campaign.name);
        setCampaignId(campaign.id);
      } else {
        console.log("No campaign found or error:", campaignError);
        console.log("All campaigns for user:", campaigns);
        setCampaignName(null);
        setCampaignId(null);
      }
      // Fetch all OCR providers (api_keys) for this user
      const { data: apiKeys, error: apiKeysError } = await supabase
        .from('api_keys')
        .select('provider')
        .eq('user_id', session.user.id)
        .eq('is_active', true);
      if (!apiKeysError && apiKeys && Array.isArray(apiKeys)) {
        // Map provider values to labels (if you want pretty labels)
        const providerLabelMap: Record<string, string> = {
          'anthropic-claude': 'Anthropic Claude 3',
          'azure-vision': 'Azure Computer Vision',
          'aws-textract': 'AWS Textract',
          'OPENAI_API_KEY': `OpenAI ${process.env.OPENAI_MODEL || 'gpt-4o-mini'}`,
          'GEMINI_API_KEY': `Google ${process.env.GEMINI_MODEL || 'gemini-1.5-flash'}`,
          'MISTRAL_API_KEY': `Mistral ${process.env.MISTRAL_MODEL || 'mistral-small'}`,
        };
        const uniqueProviders = Array.from(new Set(apiKeys.map((k: { provider: string }) => k.provider)));
        setOcrProviders(uniqueProviders.map((value) => ({ value, label: providerLabelMap[value] || value })));
        
        // Set provider based on user preference or first available
        if (!ocrProvider && uniqueProviders.length > 0) {
          // Check for stored preference
          const storedProvider = localStorage.getItem(`ocr_provider_${session.user.id}`);
          const preferredProvider = storedProvider && uniqueProviders.includes(storedProvider) 
            ? storedProvider 
            : uniqueProviders[0];
          setOcrProvider(preferredProvider);
        }
      } else {
        setOcrProviders([]);
        setOcrProvider("");
      }
      setLoading(false);
    };
    checkAuthAndFetchCampaignAndOcr();
  }, [router, supabase, ocrProvider]);

  useEffect(() => {
    if (campaignId && user) {
      fetchRegistrationData();
    }
  }, [campaignId, user, fetchRegistrationData]);

  // Fetch mapped matches when campaign changes
  useEffect(() => {
    if (campaignId) {
      fetchMappedMatches();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  const fetchMappedMatches = async () => {
    if (!campaignId) return;
    try {
      const { data, error } = await supabase
        .from('registration_matches_mapped')
        .select('*')
        .eq('campaign_id', campaignId)
        .order('match_rank', { ascending: true });
      if (error) {
        console.error('Error fetching mapped matches:', error);
        setMappedMatches([]);
      } else {
        setMappedMatches(data || []);
      }
    } catch (error) {
      console.error('Error fetching mapped matches:', error);
      setMappedMatches([]);
    } finally {
      // setMatchingLoading(false); // This line was removed from the new_code
    }
  };

  useEffect(() => {
    // Fetch config.json from public directory
    fetch('/config.json')
      .then(res => res.json())
      .then(setConfig)
      .catch(() => setConfig(null));
  }, []);

  const handleOcrProviderChange = (value: string) => {
    setOcrProvider(value)
    // Store the user's preference in localStorage
    if (user) {
      localStorage.setItem(`ocr_provider_${user.id}`, value);
    }
  }

  const cropCanvasVertically = (canvas: HTMLCanvasElement, topCrop: number, bottomCrop: number): HTMLCanvasElement => {
    const height = canvas.height;
    const width = canvas.width;
    const cropTop = Math.floor(height * topCrop);
    const cropBottom = Math.floor(height * bottomCrop);
    const cropHeight = cropBottom - cropTop;
    const croppedCanvas = document.createElement('canvas');
    croppedCanvas.width = width;
    croppedCanvas.height = cropHeight;
    const ctx = croppedCanvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(canvas, 0, cropTop, width, cropHeight, 0, 0, width, cropHeight);
    }
    return croppedCanvas;
  };

  // Utility: Convert a canvas to greyscale
  function convertCanvasToGreyscale(canvas: HTMLCanvasElement): HTMLCanvasElement {
    const ctx = canvas.getContext('2d');
    if (!ctx) return canvas;
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      // Standard luminance formula
      const grey = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      data[i] = data[i + 1] = data[i + 2] = grey;
    }
    ctx.putImageData(imageData, 0, 0);
    return canvas;
  }

  const handlePetitionUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log("handlePetitionUpload called", event.target.files);
    setIsConverting(true);
    const files = Array.from(event.target.files || []);
    const processedFiles: File[] = [];

    if (!config) {
      console.log('Config not loaded:', config);
      toast.error('Configuration not loaded. Please try again.');
      setIsConverting(false);
      return;
    }

    for (const file of files) {
      if (file.type === "application/pdf") {
        // Convert PDF to images
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const viewport = page.getViewport({ scale: 2 });
          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          await page.render({ canvasContext: context, viewport }).promise;
          // Crop the canvas vertically
          const croppedCanvas = cropCanvasVertically(canvas, config.TOP_CROP, config.BOTTOM_CROP);
          // Convert to greyscale
          const greyscaleCanvas = convertCanvasToGreyscale(croppedCanvas);
          // Convert greyscale canvas to blob
          const blob: Blob = await new Promise((resolve) =>
            greyscaleCanvas.toBlob(resolve as BlobCallback, "image/png")
          );
          // Create a File object for each page
          const imageFile = new File(
            [blob],
            `${file.name.replace(/\.pdf$/, "")}_page${i}.png`,
            { type: "image/png" }
          );
          processedFiles.push(imageFile);
        }
      } else {
        // Image file, crop as well
        const img = document.createElement('img');
        const url = URL.createObjectURL(file);
        await new Promise((resolve, reject) => {
          img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            if (ctx) ctx.drawImage(img, 0, 0);
            // Crop the canvas vertically
            const croppedCanvas = cropCanvasVertically(canvas, config.TOP_CROP, config.BOTTOM_CROP);
            // Convert to greyscale
            const greyscaleCanvas = convertCanvasToGreyscale(croppedCanvas);
            greyscaleCanvas.toBlob((blob) => {
              if (blob) {
                const croppedFile = new File(
                  [blob],
                  file.name.replace(/\.(jpg|jpeg|png)$/i, '') + '_cropped.png',
                  { type: 'image/png' }
                );
                processedFiles.push(croppedFile);
                URL.revokeObjectURL(url);
                resolve(null);
              } else {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to crop image.'));
              }
            }, 'image/png');
          };
          img.onerror = reject;
          img.src = url;
        });
      }
    }
    console.log("Processed files:", processedFiles);
    setUploadedPetitions((prev) => [...prev, ...processedFiles]);
    setIsConverting(false);
  };

  const removePetition = (index: number) => {
    setUploadedPetitions((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUploadPetitions = async () => {
    console.log("handleUploadPetitions called");
    console.log("user:", user);
    console.log("campaignId:", campaignId);
    if (!user || !campaignId) {
      console.log("Early return: user or campaignId is missing");
      toast.error("Please ensure you are logged in and have an active campaign.");
      return;
    }
    setUploading(true);
    setUploadSuccess(false);
    try {
      for (const file of uploadedPetitions) {
        const path = `${user.id}/${campaignId}/${file.name}`;
        console.log("Uploading file:", file.name, "to path:", path);
        const { error } = await supabase.storage.from("petitions").upload(path, file, { upsert: true });
        if (error) {
          console.error("Error uploading file:", file.name, error.message);
          toast.error(`Error uploading file ${file.name}: ${error.message}`);
        } else {
          console.log("Successfully uploaded:", file.name);
        }
      }
      setUploadSuccess(true);
      setUploadedFilesForOcr([...uploadedPetitions]);
      setUploadedPetitions([]); // Clear the files from the UI after upload
    } catch (err) {
      console.error("Unexpected error during upload:", err);
      toast.error("Unexpected error during upload: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setUploading(false);
    }
  };

  const handleFuzzyMatching = async () => {
    if (!user || !campaignId) {
      toast.error('Please ensure you have an active campaign.');
      return;
    }

    setIsFuzzyMatching(true);
    try {
      toast('Fuzzy matching started... (this will replace existing matches)');
              const { data: matchResult, error: matchError } = await supabase.rpc('insert_top_matches', { 
          campaign_id_input: campaignId
        });
      if (matchError) {
        toast.error('Error running fuzzy matching: ' + matchError.message);
      } else {
        toast.success('Fuzzy matching complete! ' + (matchResult || 'Previous matches replaced.'));
        // Refresh mapped matches after matching
        await fetchMappedMatches();
      }
    } catch (err) {
      toast.error('Error running fuzzy matching: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsFuzzyMatching(false);
    }
  };

  const handleProcessWithOcr = async () => {
    if (!user || !campaignId || !ocrProvider || uploadedFilesForOcr.length === 0) {
      toast.error('Please ensure you have uploaded files and selected an OCR provider.');
      return;
    }

    setIsProcessing(true);
    setOcrProgress(0);
    setOcrError(null);
    setOcrResults([]);

    try {
      // 1. Convert uploaded files to base64
      const base64Images = await Promise.all(
        uploadedFilesForOcr.map(file => encodeImageToBase64(file))
      );

      // 2. Call OCR API with batching and progress
      const results = await callOcrApi(
        base64Images,
        ocrPrompt,
        ocrProvider
      );

      // 3. Flatten results and add metadata
      const allResults: (OCRResult & { filename: string; campaign_id: string; user_id: string })[] = [];
      results.forEach((imageResults, imageIndex) => {
        imageResults.forEach((entry, rowIndex) => {
          allResults.push({
            ...(entry as OCRResult),
            page_number: imageIndex + 1,
            row_number: rowIndex + 1,
            filename: uploadedFilesForOcr[imageIndex]?.name || "unknown",
            campaign_id: campaignId!,
            user_id: user.id,
          });
        });
      });

      // 4. Insert into Supabase
      const { success, error } = await insertOcrResultsToSupabase(allResults, 'registration_data');

      if (success) {
        setOcrResults(allResults);
        setOcrProgress(100);
        toast.success(`OCR processing complete! Processed ${allResults.length} entries. Previous data replaced.`);
        // Clear the stored files after successful processing
        setUploadedFilesForOcr([]);
        // Refresh the registration data to show the new entries
        await fetchRegistrationData();
        
        // Note: Fuzzy matching is now manual - use the "Run Fuzzy Matching" button when ready
      } else {
        setOcrError(error && typeof error === 'object' && 'message' in error ? (error as Error).message : 'Failed to insert results into database');
      }
    } catch (error) {
      console.error('OCR processing error:', error);
      setOcrError((error as Error).message);
    } finally {
      setIsProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-red-50">
        <Navbar showAuthButtons />
        <div className="container mx-auto px-4 py-16 flex items-center justify-center">
          <div>Loading your campaign dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar showAuthButtons user={user ?? undefined} />
      <div className="flex">
        {/* Main Content - Full Signature Data Table */}
        <div className="flex-1 ml-72 bg-white">
          <div className="h-[calc(100vh-4rem)] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-200 bg-slate-50">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Database className="h-5 w-5 text-slate-600" />
                Signature Data
              </h2>
              <p className="text-sm text-slate-600 mt-1">Processed signature information</p>
            </div>
            <div className="flex-1 overflow-auto">
              <DataTable
                dataLoading={dataLoading}
                registrationData={registrationData}
                mappedMatches={mappedMatches}
                selectedMatchRanks={selectedMatchRanks}
                setSelectedMatchRanks={setSelectedMatchRanks}
                ocrResults={ocrResults}
              />
            </div>
            <div className="p-4 border-t border-slate-200 bg-slate-50">
              <div className="flex justify-between items-center text-sm text-slate-600">
                <span>
                  {dataLoading 
                    ? 'Loading...' 
                    : `Showing ${registrationData.length > 0 ? registrationData.length : 0} of ${registrationData.length} registration records`
                  }
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled>
                    Previous
                  </Button>
                  <Button variant="outline" size="sm" disabled>
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Left Sidebar */}
        <Sidebar
          campaignName={campaignName ?? undefined}
          ocrProvider={ocrProvider}
          ocrProviders={ocrProviders}
          handleOcrProviderChange={handleOcrProviderChange}
          ocrPrompt={ocrPrompt}
          setOcrPrompt={setOcrPrompt}
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
          handleFuzzyMatching={handleFuzzyMatching}
          isFuzzyMatching={isFuzzyMatching}
        />
      </div>
    </div>
  )
}
