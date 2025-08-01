import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";
import Papa from "https://esm.sh/papaparse@5.4.1";
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type"
};
serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  // Get the user's access token from the Authorization header
  const authHeader = req.headers.get("Authorization");
  const accessToken = authHeader?.replace("Bearer ", "");
  if (!accessToken) {
    return new Response(JSON.stringify({ error: 'Missing access token in Authorization header.' }), { status: 401, headers: corsHeaders });
  }

  let filePath, campaign_id, user_id;
  try {
    const body = await req.json();
    filePath = body.filePath;
    campaign_id = body.campaign_id;
    user_id = body.user_id;
    if (!filePath || !campaign_id || !user_id) {
      return new Response(JSON.stringify({ error: 'Missing required fields in request body.', body }), { status: 400, headers: corsHeaders });
    }
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Invalid request body', details: String(err) }), { status: 400, headers: corsHeaders });
  }

  // Create a Supabase client as the user
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL'),
    Deno.env.get('SUPABASE_ANON_KEY'),
    { global: { headers: { Authorization: `Bearer ${accessToken}` } } }
  );

  // Download the file from storage
  const { data: fileData, error: downloadError } = await supabase
    .storage
    .from('voter-files')
    .download(filePath);

  if (downloadError || !fileData) {
    return new Response(JSON.stringify({ error: 'Failed to download file from storage', details: downloadError }), { status: 400, headers: corsHeaders });
  }

  // Read file as text
  let csvText = '';
  try {
    csvText = await fileData.text();
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Failed to read file as text', details: String(err) }), { status: 400, headers: corsHeaders });
  }

  // Remove spaces between commas (and trim each line)
  csvText = csvText
    .split('\n')
    .map(line => line.trim().replace(/ *, */g, ','))
    .join('\n');

  // Parse CSV
  let parsed;
  try {
    parsed = Papa.parse(csvText, { header: true, skipEmptyLines: true });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'CSV parse threw exception', details: String(err) }), { status: 400, headers: corsHeaders });
  }
  if (parsed.errors.length > 0) {
    return new Response(JSON.stringify({ error: 'CSV parse error', details: parsed.errors }), { status: 400, headers: corsHeaders });
  }

  // Clean and prepare records
  const records = parsed.data.map((row) => {
    // Trim whitespace and treat empty/whitespace-only fields as null
    const clean = (val) => {
      if (typeof val !== 'string') return val;
      const trimmed = val.trim();
      return trimmed === '' ? null : trimmed;
    };
    return {
      campaign_id,
      first_name: clean(row.First_Name),
      last_name: clean(row.Last_Name),
      street_number: clean(row.Street_Number),
      street_name: clean(row.Street_Name),
      street_type: clean(row.Street_Type),
      street_dir_suffix: clean(row.Street_Dir_Suffix),
    };
  });

  // Insert records into voter_records in batches
  const batchSize = parseInt(Deno.env.get('VOTER_FILE_BATCH_SIZE') || '1000');
  let insertError = null;
  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);
    try {
      const { error } = await supabase
        .from('voter_records')
        .insert(batch);
      if (error) {
        insertError = error;
        break; // Stop on first error
      }
    } catch (err) {
      insertError = err;
      break;
    }
  }

  // Update file_processing_status
  try {
    await supabase.from('file_processing_status').insert({
      user_id,
      campaign_id,
      file_name: filePath.split('/').pop(),
      status: insertError ? 'error' : 'completed',
      records_processed: records.length,
      error_message: insertError ? insertError.message : null,
      completed_at: new Date().toISOString(),
    });
  } catch (err) {
    // Log but do not fail the function if this insert fails
  }

  if (insertError) {
    return new Response(JSON.stringify({ error: 'Insert error', details: insertError }), { status: 500, headers: corsHeaders });
  }

  return new Response(JSON.stringify({ message: 'Success', records_processed: records.length }), { status: 200, headers: corsHeaders });
}); 