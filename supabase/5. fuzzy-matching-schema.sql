-- Note: pg_trgm extension needs to be enabled in Supabase dashboard
-- Go to Database > Extensions and enable 'pg_trgm'
-- For now, we'll use a simpler similarity function

CREATE TABLE IF NOT EXISTS registration_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID,
    registered_name TEXT,
    name_distance INTEGER,
    registered_address TEXT,
    address_distance INTEGER,
    match_rank INTEGER,
    campaign_id UUID,
    created_at TIMESTAMP DEFAULT now()
);

-- Add foreign key constraint if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_registration' 
        AND table_name = 'registration_matches'
    ) THEN
        ALTER TABLE registration_matches
        ADD CONSTRAINT fk_registration
        FOREIGN KEY (registration_id)
        REFERENCES registration_data(id)
        ON DELETE CASCADE;
    END IF;
END $$;

-- Enable RLS
ALTER TABLE registration_matches ENABLE ROW LEVEL SECURITY;

-- RLS policies for registration_matches (create if they don't exist)
DO $$ 
BEGIN
    -- Insert policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'registration_matches' 
        AND policyname = 'Allow user to insert own registration matches'
    ) THEN
        CREATE POLICY "Allow user to insert own registration matches"
        ON registration_matches FOR INSERT
        WITH CHECK (
          EXISTS (
            SELECT 1 FROM campaign 
            WHERE campaign.id = registration_matches.campaign_id 
            AND campaign.user_id = auth.uid()
          )
        );
    END IF;

    -- Select policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'registration_matches' 
        AND policyname = 'Allow user to select own registration matches'
    ) THEN
        CREATE POLICY "Allow user to select own registration matches"
        ON registration_matches FOR SELECT
        USING (
          EXISTS (
            SELECT 1 FROM campaign 
            WHERE campaign.id = registration_matches.campaign_id 
            AND campaign.user_id = auth.uid()
          )
        );
    END IF;

    -- Update policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'registration_matches' 
        AND policyname = 'Allow user to update own registration matches'
    ) THEN
        CREATE POLICY "Allow user to update own registration matches"
        ON registration_matches FOR UPDATE
        USING (
          EXISTS (
            SELECT 1 FROM campaign 
            WHERE campaign.id = registration_matches.campaign_id 
            AND campaign.user_id = auth.uid()
          )
        );
    END IF;

    -- Delete policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'registration_matches' 
        AND policyname = 'Allow user to delete own registration matches'
    ) THEN
        CREATE POLICY "Allow user to delete own registration matches"
        ON registration_matches FOR DELETE
        USING (
          EXISTS (
            SELECT 1 FROM campaign 
            WHERE campaign.id = registration_matches.campaign_id 
            AND campaign.user_id = auth.uid()
          )
        );
    END IF;
END $$;

-- Function to insert top 5 fuzzy-matched registration matches for a given campaign
CREATE OR REPLACE FUNCTION insert_top_matches(campaign_id_input UUID)
RETURNS void AS $$
BEGIN
  -- Insert new matches, avoiding duplicates by checking existing combinations
  INSERT INTO registration_matches (
    id,
    registration_id,
    registered_name,
    name_distance,
    registered_address,
    address_distance,
    match_rank,
    campaign_id
  )
  WITH joined_data AS (
    SELECT
      rd.id AS registration_id,
      (vr.first_name || ' ' || vr.last_name) AS registered_name,
      -- Simple string similarity using length difference and case-insensitive comparison
      CASE 
        WHEN LOWER(vr.first_name || ' ' || vr.last_name) = LOWER(rd.name) THEN 0
        WHEN LOWER(vr.first_name || ' ' || vr.last_name) LIKE '%' || LOWER(rd.name) || '%' 
             OR LOWER(rd.name) LIKE '%' || LOWER(vr.first_name || ' ' || vr.last_name) || '%' THEN 1
        ELSE ABS(LENGTH(vr.first_name || ' ' || vr.last_name) - LENGTH(rd.name)) + 10
      END AS name_distance,
      (
        COALESCE(vr.street_number, '') || ' ' ||
        COALESCE(vr.street_name, '') || ' ' ||
        COALESCE(vr.street_type, '') || ' ' ||
        COALESCE(vr.street_dir_suffix, '')
      ) AS registered_address,
      -- Simple string similarity for addresses
      CASE 
        WHEN LOWER(
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ) = LOWER(rd.address) THEN 0
        WHEN LOWER(
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ) LIKE '%' || LOWER(rd.address) || '%' 
             OR LOWER(rd.address) LIKE '%' || LOWER(
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ) || '%' THEN 1
        ELSE ABS(LENGTH(
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ) - LENGTH(rd.address)) + 10
      END AS address_distance,
      rd.campaign_id
    FROM
      registration_data rd
    JOIN
      voter_records vr ON vr.campaign_id = rd.campaign_id
    WHERE
      rd.campaign_id = campaign_id_input
  ),
  ranked AS (
    SELECT
      registration_id,
      registered_name,
      name_distance,
      registered_address,
      address_distance,
      campaign_id,
      ROW_NUMBER() OVER (
        PARTITION BY registration_id
        ORDER BY (name_distance + address_distance)
      ) AS match_rank
    FROM joined_data
  )
  SELECT
    gen_random_uuid() AS id,
    registration_id,
    registered_name,
    name_distance,
    registered_address,
    address_distance,
    match_rank,
    campaign_id
  FROM ranked
  WHERE match_rank <= 5;
END;
$$ LANGUAGE plpgsql;

-- Ultra-optimized function that processes one registration at a time to prevent timeouts
CREATE OR REPLACE FUNCTION insert_top_matches_batched(campaign_id_input UUID, batch_size INTEGER DEFAULT 10)
RETURNS TEXT AS $$
DECLARE
  total_registrations INTEGER;
  processed_count INTEGER := 0;
  batch_count INTEGER := 0;
  start_time TIMESTAMP;
  end_time TIMESTAMP;
  registration_record RECORD;
BEGIN
  start_time := NOW();
  
  -- First, delete existing matches for this campaign
  DELETE FROM registration_matches WHERE campaign_id = campaign_id_input;
  
  -- Get total count of registrations for this campaign
  SELECT COUNT(*) INTO total_registrations 
  FROM registration_data 
  WHERE campaign_id = campaign_id_input;
  
  -- Process registrations one by one to avoid massive cross-joins
  FOR registration_record IN 
    SELECT id, name, address, campaign_id
    FROM registration_data 
    WHERE campaign_id = campaign_id_input
    ORDER BY id
  LOOP
    processed_count := processed_count + 1;
    
    -- Insert top 5 matches for this single registration
    INSERT INTO registration_matches (
      id,
      registration_id,
      registered_name,
      name_distance,
      registered_address,
      address_distance,
      match_rank,
      campaign_id
    )
    WITH single_registration AS (
      SELECT 
        registration_record.id AS registration_id,
        registration_record.name,
        registration_record.address,
        registration_record.campaign_id
    ),
    joined_data AS (
      SELECT
        sr.registration_id,
        (vr.first_name || ' ' || vr.last_name) AS registered_name,
        -- Simple string similarity using length difference and case-insensitive comparison
        CASE 
          WHEN LOWER(vr.first_name || ' ' || vr.last_name) = LOWER(sr.name) THEN 0
          WHEN LOWER(vr.first_name || ' ' || vr.last_name) LIKE '%' || LOWER(sr.name) || '%' 
               OR LOWER(sr.name) LIKE '%' || LOWER(vr.first_name || ' ' || vr.last_name) || '%' THEN 1
          ELSE ABS(LENGTH(vr.first_name || ' ' || vr.last_name) - LENGTH(sr.name)) + 10
        END AS name_distance,
        (
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ) AS registered_address,
        -- Simple string similarity for addresses
        CASE 
          WHEN LOWER(
            COALESCE(vr.street_number, '') || ' ' ||
            COALESCE(vr.street_name, '') || ' ' ||
            COALESCE(vr.street_type, '') || ' ' ||
            COALESCE(vr.street_dir_suffix, '')
          ) = LOWER(sr.address) THEN 0
          WHEN LOWER(
            COALESCE(vr.street_number, '') || ' ' ||
            COALESCE(vr.street_name, '') || ' ' ||
            COALESCE(vr.street_type, '') || ' ' ||
            COALESCE(vr.street_dir_suffix, '')
          ) LIKE '%' || LOWER(sr.address) || '%' 
               OR LOWER(sr.address) LIKE '%' || LOWER(
            COALESCE(vr.street_number, '') || ' ' ||
            COALESCE(vr.street_name, '') || ' ' ||
            COALESCE(vr.street_type, '') || ' ' ||
            COALESCE(vr.street_dir_suffix, '')
          ) || '%' THEN 1
          ELSE ABS(LENGTH(
            COALESCE(vr.street_number, '') || ' ' ||
            COALESCE(vr.street_name, '') || ' ' ||
            COALESCE(vr.street_type, '') || ' ' ||
            COALESCE(vr.street_dir_suffix, '')
          ) - LENGTH(sr.address)) + 10
        END AS address_distance,
        sr.campaign_id
      FROM
        single_registration sr
      JOIN
        voter_records vr ON vr.campaign_id = sr.campaign_id
    ),
    ranked AS (
      SELECT
        registration_id,
        registered_name,
        name_distance,
        registered_address,
        address_distance,
        campaign_id,
        ROW_NUMBER() OVER (
          ORDER BY (name_distance + address_distance)
        ) AS match_rank
      FROM joined_data
    )
    SELECT
      gen_random_uuid() AS id,
      registration_id,
      registered_name,
      name_distance,
      registered_address,
      address_distance,
      match_rank,
      campaign_id
    FROM ranked
    WHERE match_rank <= 5;
    
    -- Add a small delay every 10 registrations to prevent overwhelming the database
    IF processed_count % 10 = 0 THEN
      PERFORM pg_sleep(0.05);
    END IF;
  END LOOP;
  
  end_time := NOW();
  
  RETURN 'Processed ' || total_registrations || ' registrations individually. Duration: ' || (end_time - start_time);
END;
$$ LANGUAGE plpgsql;

-- Example usage (uncomment and replace with actual campaign_id when needed):
-- SELECT insert_top_matches('your-campaign-id-here');

-- View to map registration matches to registration data

CREATE OR REPLACE VIEW registration_matches_mapped AS
SELECT
    rm.id,
    rm.registration_id,
    rd.name AS petition_name,
    rm.registered_name,
    rm.name_distance,
    rd.address AS petition_address,
    rm.registered_address,
    rm.address_distance,
    rm.match_rank,
    rm.campaign_id,
    rm.created_at
FROM
    registration_matches rm
JOIN
    registration_data rd
ON
    rm.registration_id = rd.id;

-- View to select all registration matches for a given campaign

CREATE OR REPLACE VIEW registration_matches_mapped_campaign AS

SELECT
  petition_name,
  registered_name,
  name_distance,
  petition_address,
  registered_address,
  address_distance,
  match_rank
FROM registration_matches_mapped