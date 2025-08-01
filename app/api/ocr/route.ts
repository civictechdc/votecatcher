import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { decrypt } from "@/lib/encryption";

interface OCREntry {
  Name: string;
  Address: string;
  Date: string;
  Ward: number;
}

export async function POST(req: NextRequest) {
  try {
    const supabase = await createClient();
    
    // Get the authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { base64Images, prompt, provider } = await req.json();

    if (!base64Images || !Array.isArray(base64Images) || base64Images.length === 0) {
      return NextResponse.json({ error: 'No images provided' }, { status: 400 });
    }

    if (!provider) {
      return NextResponse.json({ error: 'Missing provider' }, { status: 400 });
    }

    // 1. Fetch the API key for this user/provider
    const { data: apiKeyRow, error } = await supabase
      .from('api_keys')
      .select('api_key')
      .eq('user_id', user.id)
      .eq('provider', provider)
      .eq('is_active', true)
      .single();

    if (error || !apiKeyRow) {
      return NextResponse.json({ error: 'API key not found or inactive' }, { status: 403 });
    }

    const apiKey = decrypt(apiKeyRow.api_key);

    // 2. Process each image with the appropriate OCR provider
    const results: OCREntry[][] = [];

    for (let i = 0; i < base64Images.length; i++) {
      const base64Image = base64Images[i];
      try {
        const ocrResult = await callOcrProvider(base64Image, prompt, apiKey, provider);
        results.push(ocrResult);
        
        // Add delay between requests for Gemini free tier (15 req/min = 4 seconds between requests)
        if (provider === 'GEMINI_API_KEY' && i < base64Images.length - 1) {
          console.log(`Waiting 4 seconds before next Gemini request... (${i + 1}/${base64Images.length})`);
          await new Promise(resolve => setTimeout(resolve, 4000));
        }
      } catch (error) {
        console.error('OCR processing error:', error);
        // Continue with other images even if one fails
        results.push([]);
      }
    }

    return NextResponse.json({ results });
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json({ error: (error as Error).message }, { status: 500 });
  }
}

async function callOcrProvider(
  base64Image: string, 
  prompt: string, 
  apiKey: string, 
  provider: string
): Promise<OCREntry[]> {
  // Remove the data:image/jpeg;base64, prefix if present
  const cleanBase64 = base64Image.replace(/^data:image\/[a-z]+;base64,/, '');

  switch (provider) {
    case 'OPENAI_API_KEY':
      return await callOpenAI(cleanBase64, prompt, apiKey);
    case 'GEMINI_API_KEY':
      return await callGemini(cleanBase64, prompt, apiKey);
    case 'MISTRAL_API_KEY':
      return await callMistral(cleanBase64, prompt, apiKey);
    default:
      throw new Error(`Unsupported provider: ${provider}`);
  }
}

async function callOpenAI(base64Image: string, prompt: string, apiKey: string): Promise<OCREntry[]> {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
                  body: JSON.stringify({
          model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
          messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: prompt,
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`,
              },
            },
          ],
        },
      ],
      max_tokens: parseInt(process.env.OCR_MAX_TOKENS || '1000'),
    }),
  });

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error(`OpenAI API rate limit exceeded. Please wait a moment and try again.`);
    } else if (response.status === 401) {
      throw new Error(`OpenAI API authentication failed. Please check your API key.`);
    } else if (response.status === 400) {
      throw new Error(`OpenAI API request error. Please check your input.`);
    } else {
      throw new Error(`OpenAI API error: ${response.statusText}`);
    }
  }

  const data = await response.json();
  const content = data.choices[0].message.content;
  
  // Remove code block markers if present
  const cleaned = content
    .replace(/^```[a-zA-Z]*\n?/, '') // Remove opening ``` and optional language
    .replace(/```$/, '')
    .trim();

  // Parse the JSON response
  try {
    const parsed = JSON.parse(cleaned);
    return parsed || [];
  } catch {
    console.error('Failed to parse OpenAI response:', content);
    return [];
  }
}

async function callGemini(base64Image: string, prompt: string, apiKey: string): Promise<OCREntry[]> {
  const model = process.env.GEMINI_MODEL || 'gemini-1.5-flash';
  
  // Retry logic for rate limits
  const maxRetries = 3;
  let lastError: Error | null = null;
  
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: prompt,
                },
                {
                  inline_data: {
                    mime_type: 'image/jpeg',
                    data: base64Image,
                  },
                },
              ],
            },
          ],
        }),
      });

      if (!response.ok) {
        if (response.status === 429) {
          lastError = new Error(`Gemini API rate limit exceeded (attempt ${attempt}/${maxRetries}). Please wait a moment and try again.`);
          if (attempt < maxRetries) {
            console.log(`Rate limit hit, waiting ${attempt * 5} seconds before retry...`);
            await new Promise(resolve => setTimeout(resolve, attempt * 5000));
            continue;
          }
          throw lastError;
        } else if (response.status === 401) {
          throw new Error(`Gemini API authentication failed. Please check your API key.`);
        } else if (response.status === 400) {
          throw new Error(`Gemini API request error. Please check your input.`);
        } else {
          throw new Error(`Gemini API error: ${response.statusText}`);
        }
      }

      const data = await response.json();
      const content = data.candidates[0].content.parts[0].text;
      
      console.log('Raw Gemini content:', JSON.stringify(content));
      
      // Clean the response - extract JSON from markdown code blocks
      let cleaned = content;
      
      // Try to extract JSON from markdown code blocks
      const jsonMatch = content.match(/```(?:json)?\s*(\[[\s\S]*?\])\s*```/);
      if (jsonMatch) {
        cleaned = jsonMatch[1].trim();
      } else {
        // Fallback: remove markdown code blocks if present
        cleaned = content
          .replace(/^```[a-zA-Z]*\n?/, '') // Remove opening ``` and optional language
          .replace(/```[\s\S]*$/, '') // Remove everything from closing ``` to end
          .trim();
      }
      
      console.log('Cleaned content length:', cleaned.length);
      console.log('Cleaned content first 100 chars:', cleaned.substring(0, 100));
      
      try {
        const parsed = JSON.parse(cleaned);
        console.log('Successfully parsed Gemini response:', parsed);
        return parsed || [];
      } catch (parseError) {
        console.error('Failed to parse Gemini response:', content);
        console.error('Cleaned content:', cleaned);
        console.error('Parse error:', parseError);
        
        // Try parsing the original content as fallback
        try {
          const fallbackParsed = JSON.parse(content);
          console.log('Fallback parse successful:', fallbackParsed);
          return fallbackParsed || [];
        } catch (fallbackError) {
          console.error('Fallback parse also failed:', fallbackError);
          return [];
        }
      }
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxRetries) {
        console.log(`Attempt ${attempt} failed, retrying...`);
        continue;
      }
    }
  }
  
  // If we get here, all retries failed
  throw lastError || new Error('All retry attempts failed');
}

async function callMistral(base64Image: string, prompt: string, apiKey: string): Promise<OCREntry[]> {
  const model = process.env.MISTRAL_MODEL || 'mistral-small';
  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: model,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: prompt,
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`,
              },
            },
          ],
        },
      ],
      max_tokens: parseInt(process.env.OCR_MAX_TOKENS || '1000'),
    }),
  });

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error(`Mistral API rate limit exceeded. Please wait a moment and try again.`);
    } else if (response.status === 401) {
      throw new Error(`Mistral API authentication failed. Please check your API key.`);
    } else if (response.status === 400) {
      throw new Error(`Mistral API request error. Please check your input.`);
    } else {
      throw new Error(`Mistral API error: ${response.statusText}`);
    }
  }

  const data = await response.json();
  const content = data.choices[0].message.content;
  
  try {
    const parsed = JSON.parse(content);
    return parsed || [];
  } catch {
    console.error('Failed to parse Mistral response:', content);
    return [];
  }
} 