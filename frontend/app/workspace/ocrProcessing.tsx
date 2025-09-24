/**
 * Encodes an image File as a base64 string (no cropping, no PDF support)
 * @param file - Image file (PNG, JPG, etc)
 * @returns Promise<string> - base64-encoded image (PNG format)
 */
export async function encodeImageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = document.createElement('img');
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.drawImage(img, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');
      URL.revokeObjectURL(url);
      resolve(dataUrl.split(',')[1]); // base64 part only
    };
    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(e);
    };
    img.src = url;
  });
}

/**
 * Crops a canvas vertically according to topCrop and bottomCrop (fractions of height)
 */
function cropCanvasVertically(
  canvas: HTMLCanvasElement,
  topCrop: number,
  bottomCrop: number
): HTMLCanvasElement {
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
}

/**
 * Converts a canvas to greyscale in-place.
 */
function convertCanvasToGreyscale(canvas: HTMLCanvasElement): HTMLCanvasElement {
  const ctx = canvas.getContext('2d');
  if (!ctx) return canvas;
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const grey = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    data[i] = data[i + 1] = data[i + 2] = grey;
  }
  ctx.putImageData(imageData, 0, 0);
  return canvas;
}

import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf";
pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

import { createClient } from "@/lib/supabase/client";
import type { OCRResult } from "./ocrApi";
const supabase = createClient();

/**
 * Processes a list of files (images or PDFs), applies cropping and greyscale, and returns processed File objects.
 * @param files - Array of File objects (images or PDFs)
 * @param config - Cropping config with TOP_CROP and BOTTOM_CROP
 * @returns Promise<File[]> - Array of processed File objects
 */
export async function processFilesForOcr(
  files: File[],
  config: { TOP_CROP: number; BOTTOM_CROP: number }
): Promise<File[]> {
  const processedFiles: File[] = [];
  for (const file of files) {
    if (file.type === "application/pdf") {
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
        const croppedCanvas = cropCanvasVertically(canvas, config.TOP_CROP, config.BOTTOM_CROP);
        const greyscaleCanvas = convertCanvasToGreyscale(croppedCanvas);
        const blob: Blob = await new Promise((resolve) =>
          greyscaleCanvas.toBlob(resolve as BlobCallback, "image/png")
        );
        const imageFile = new File(
          [blob],
          `${file.name.replace(/\.pdf$/, "")}_page${i}.png`,
          { type: "image/png" }
        );
        processedFiles.push(imageFile);
      }
    } else {
      const img = document.createElement('img');
      const url = URL.createObjectURL(file);
      await new Promise((resolve, reject) => {
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          if (ctx) ctx.drawImage(img, 0, 0);
          const croppedCanvas = cropCanvasVertically(canvas, config.TOP_CROP, config.BOTTOM_CROP);
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
  return processedFiles;
}

/**
 * Uploads an array of File objects to Supabase Storage in the petitions bucket.
 * @param files - Array of File objects
 * @param userId - User ID
 * @param campaignId - Campaign ID
 * @returns Promise<void>
 */
export async function uploadFilesToSupabase(
  files: File[],
  userId: string,
  campaignId: string
): Promise<void> {
  for (const file of files) {
    const path = `${userId}/${campaignId}/${file.name}`;
    await supabase.storage.from("petitions").upload(path, file, { upsert: true });
  }
}

/**
 * Adds page_number, row_number, and filename metadata to recognized signatures.
 * @param initialData - Array of recognized signature objects
 * @param pageNo - The page_number (0-based, will be incremented by 1)
 * @param filename - The name of the file
 * @returns Array of objects with metadata added
 */
export function addMetadata<T extends object>(
  initialData: T[],
  pageNo: number,
  filename: string
): (T & { page_number: number; row_number: number; filename: string })[] {
  return initialData.map((data, row) => ({
    ...data,
    page_number: pageNo + 1,
    row_number: row + 1,
    "filename": filename,
  }));
}

/**
 * Processes a batch of base64-encoded images concurrently using an async OCR function.
 * @param encodings - Array of base64-encoded images
 * @param extractFromEncodingAsync - Async function that takes a base64 string and returns OCR result
 * @returns Promise<Array<any>> - Array of OCR results (one per image)
 */
export async function processBatchAsync<T>(
  encodings: string[],
  extractFromEncodingAsync: (encoding: string) => Promise<T>
): Promise<T[]> {
  const tasks = encodings.map(encoding => extractFromEncodingAsync(encoding));
  return Promise.all(tasks);
}

/**
 * Collects OCR data from a batch of base64-encoded images.
 * @param base64Images - Array of base64-encoded images (one per page)
 * @param filename - The name of the file (for metadata)
 * @param extractFromEncodingAsync - Async function to perform OCR on a base64 image
 * @param maxPageNum - Optional: max number of pages to process
 * @param batchSize - Number of images to process in each batch
 * @param onProgress - Optional: callback for progress updates (progress: 0-1, batch info)
 * @returns Promise<Array<any>> - Flat array of OCR results with metadata
 */
export async function collectOcrData<T extends object = OCRResult>(
  base64Images: string[],
  filename: string,
  extractFromEncodingAsync: (encoding: string) => Promise<T[]>,
  maxPageNum?: number,
  batchSize: number = 10,
  onProgress?: (progress: number, batch: number, totalBatches: number) => void
): Promise<T[]> {
  // Limit pages if needed
  const images = maxPageNum ? base64Images.slice(0, maxPageNum) : base64Images;
  const totalPages = images.length;
  const fullData: T[] = [];
  const totalBatches = Math.ceil(totalPages / batchSize);

  for (let i = 0; i < totalPages; i += batchSize) {
    const batch = images.slice(i, i + batchSize);
    // Run async batch processing
    const batchResults = await processBatchAsync(batch, extractFromEncodingAsync);

    // Add metadata for each result in the batch
    for (let pageIdx = 0; pageIdx < batchResults.length; pageIdx++) {
      const currentPage = i + pageIdx;
      const ocrData = addMetadata(batchResults[pageIdx], currentPage, filename);
      fullData.push(...ocrData);
    }

    if (onProgress) {
      onProgress(Math.min((i + batchSize) / totalPages, 1), Math.floor(i / batchSize) + 1, totalBatches);
    }
  }

  return fullData;
}

export async function insertOcrResultsToSupabase(
  ocrResults: OCRResult[],
  tableName: string = 'registration_data'
): Promise<{ success: boolean; error?: unknown }> {
  try {
    // First, delete existing OCR results for this campaign to avoid duplicates
    if (ocrResults.length > 0) {
      const campaignId = ocrResults[0].campaign_id;
      const { error: deleteError } = await supabase
        .from(tableName)
        .delete()
        .eq('campaign_id', campaignId);
      
      if (deleteError) {
        console.error('Error deleting existing OCR results:', deleteError);
        return { success: false, error: deleteError };
      }
    }

    // Then insert the new OCR results
    const { error } = await supabase.from(tableName).insert(ocrResults);
    if (error) {
      console.error('Error inserting OCR results:', error);
      return { success: false, error };
    }
    return { success: true };
  } catch (err) {
    console.error('Unexpected error in insertOcrResultsToSupabase:', err);
    return { success: false, error: err };
  }
} 