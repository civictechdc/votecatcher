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

ALTER TABLE registration_matches
ADD CONSTRAINT fk_registration
FOREIGN KEY (registration_id)
REFERENCES registration_data(id)
ON DELETE CASCADE;

-- Enable RLS
ALTER TABLE registration_matches ENABLE ROW LEVEL SECURITY;

-- RLS policies for registration_matches
CREATE POLICY "Allow user to insert own registration matches"
ON registration_matches FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = registration_matches.campaign_id 
    AND campaign.user_id = auth.uid()
  )
);

CREATE POLICY "Allow user to select own registration matches"
ON registration_matches FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = registration_matches.campaign_id 
    AND campaign.user_id = auth.uid()
  )
);

CREATE POLICY "Allow user to update own registration matches"
ON registration_matches FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = registration_matches.campaign_id 
    AND campaign.user_id = auth.uid()
  )
);

CREATE POLICY "Allow user to delete own registration matches"
ON registration_matches FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM campaign 
    WHERE campaign.id = registration_matches.campaign_id 
    AND campaign.user_id = auth.uid()
  )
);

-- Function to insert top 5 fuzzy-matched registration matches for a given campaign
CREATE OR REPLACE FUNCTION insert_top_matches(campaign_id_input UUID)
RETURNS void AS $$
BEGIN
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
      levenshtein(LOWER(vr.first_name || ' ' || vr.last_name), LOWER(rd.name)) AS name_distance,
      (
        COALESCE(vr.street_number, '') || ' ' ||
        COALESCE(vr.street_name, '') || ' ' ||
        COALESCE(vr.street_type, '') || ' ' ||
        COALESCE(vr.street_dir_suffix, '')
      ) AS registered_address,
      levenshtein(
        LOWER(
          COALESCE(vr.street_number, '') || ' ' ||
          COALESCE(vr.street_name, '') || ' ' ||
          COALESCE(vr.street_type, '') || ' ' ||
          COALESCE(vr.street_dir_suffix, '')
        ),
        LOWER(rd.address)
      ) AS address_distance,
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

SELECT insert_top_matches('5255dab2-0ba8-4070-ab83-8925a8146dd4');

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