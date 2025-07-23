/**
 * Calls the OCR API route with base64 images and returns structured OCR results
 * @param base64Images - Array of base64-encoded images
 * @param prompt - OCR prompt to send to the LLM
 * @param userId - User ID for API key lookup
 * @param provider - OCR provider (e.g., 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'MISTRAL_API_KEY')
 * @returns Promise<Array<Array<any>>> - Array of OCR results (one array per image)
 */
export async function callOcrApi(
  base64Images: string[],
  prompt: string,
  userId: string,
  provider: string
): Promise<OCRResult[][]> {
  const response = await fetch('/api/ocr', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      base64Images,
      prompt,
      userId,
      provider,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `OCR API error: ${response.statusText}`);
  }

  const data = await response.json();
  return data.results;
}

/**
 * Extracts OCR data from a single base64 image
 * @param base64Image - Base64-encoded image
 * @param prompt - OCR prompt
 * @param userId - User ID
 * @param provider - OCR provider
 * @returns Promise<Array<any>> - OCR results for the single image
 */
export async function extractFromEncodingAsync(
  base64Image: string,
  prompt: string,
  userId: string,
  provider: string
): Promise<OCRResult[]> {
  const results = await callOcrApi([base64Image], prompt, userId, provider);
  return results[0] || [];
}

export interface OCRResult {
  name: string;
  address: string;
  ward: string;
  page_number: number;
  row_number: number;
} 