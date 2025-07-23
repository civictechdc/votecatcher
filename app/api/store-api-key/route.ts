import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { encrypt } from '@/lib/encryption';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(req: NextRequest) {
  try {
    const { provider, apiKey, userId } = await req.json();
    if (!provider || !apiKey || !userId) {
      return NextResponse.json({ error: 'Missing provider, apiKey, or userId' }, { status: 400 });
    }
    const encryptedKey = encrypt(apiKey);
    const { error } = await supabase
      .from('api_keys')
      .upsert(
        { user_id: userId, provider, api_key: encryptedKey, is_active: true },
        { onConflict: 'user_id,provider' }
      );
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ error: (err instanceof Error ? err.message : 'Unknown error') }, { status: 500 });
  }
} 