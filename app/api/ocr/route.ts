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

    for (const base64Image of base64Images) {
      try {
        const ocrResult = await callOcrProvider(base64Image, prompt, apiKey, provider);
        results.push(ocrResult);
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
      model: 'gpt-4o',
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
      max_tokens: 1000,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.statusText}`);
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
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key=${apiKey}`, {
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
    throw new Error(`Gemini API error: ${response.statusText}`);
  }

  const data = await response.json();
  const content = data.candidates[0].content.parts[0].text;
  
  try {
    const parsed = JSON.parse(content);
    return parsed || [];
  } catch {
    console.error('Failed to parse Gemini response:', content);
    return [];
  }
}

async function callMistral(base64Image: string, prompt: string, apiKey: string): Promise<OCREntry[]> {
  const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'mistral-large-latest',
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
      max_tokens: 1000,
    }),
  });

  if (!response.ok) {
    throw new Error(`Mistral API error: ${response.statusText}`);
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