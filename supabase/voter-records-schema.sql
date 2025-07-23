-- Create voter_records table with simplified fields
CREATE TABLE voter_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id uuid REFERENCES campaign NOT NULL,
  first_name text,
  last_name text,
  street_number text,
  street_name text,
  street_type text,
  street_dir_suffix text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX voter_records_campaign_id_idx ON voter_records (campaign_id);
CREATE INDEX voter_records_name_idx ON voter_records (last_name, first_name);
CREATE INDEX voter_records_address_idx ON voter_records (street_name, street_number);

-- Enable RLS
ALTER TABLE voter_records ENABLE ROW LEVEL SECURITY;

-- RLS policies for voter_records (allow both user and service role)
CREATE POLICY "Allow user and service role to insert voter records"
ON voter_records FOR INSERT
WITH CHECK (
  (EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = voter_records.campaign_id 
    AND campaign.user_id = auth.uid()
  )) OR 
  auth.role() = 'service_role'
);

CREATE POLICY "Allow user to select own voter records"
ON voter_records FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = voter_records.campaign_id 
    AND campaign.user_id = auth.uid()
  )
);

-- Create file processing status table
CREATE TABLE file_processing_status (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users NOT NULL,
  campaign_id uuid REFERENCES campaign NOT NULL,
  file_name text NOT NULL,
  status text DEFAULT 'processing',
  records_processed integer DEFAULT 0,
  total_records integer,
  error_message text,
  created_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone
);

-- Enable RLS for processing status
ALTER TABLE file_processing_status ENABLE ROW LEVEL SECURITY;

-- RLS policies for file_processing_status (allow both user and service role)
CREATE POLICY "Allow user and service role to insert processing status"
ON file_processing_status FOR INSERT
WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

CREATE POLICY "Allow user to select own processing status"
ON file_processing_status FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Allow user and service role to update processing status"
ON file_processing_status FOR UPDATE
USING (auth.uid() = user_id OR auth.role() = 'service_role');

-- Create Storage bucket for voter files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('voter-files', 'voter-files', false)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies
CREATE POLICY "Allow authenticated users to upload voter files"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'voter-files' AND auth.role() = 'authenticated');

CREATE POLICY "Allow users to view their own voter files"
ON storage.objects FOR SELECT
USING (bucket_id = 'voter-files' AND auth.role() = 'authenticated');

CREATE POLICY "Allow users to update their own voter files"
ON storage.objects FOR UPDATE
USING (bucket_id = 'voter-files' AND auth.role() = 'authenticated');

CREATE POLICY "Allow users to delete their own voter files"
ON storage.objects FOR DELETE
USING (bucket_id = 'voter-files' AND auth.role() = 'authenticated');