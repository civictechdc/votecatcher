create table registration_data (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid references campaign(id) not null,
  user_id uuid references auth.users(id) not null,
  name text,
  address text,
  ward text,
  page_number integer,
  row_number integer,
  filename text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  date date
);

-- Indexes for performance
create index registration_data_campaign_id_idx on registration_data (campaign_id);
create index registration_data_name_idx on registration_data (name);
create index registration_data_address_idx on registration_data (address);
create index registration_data_page_row_idx on registration_data (page_number, row_number);

-- Enable RLS
alter table registration_data enable row level security;

-- RLS policies for registration_data
create policy "Allow user to insert own registration data"
on registration_data for insert
with check (
  exists (
    select 1 from campaign 
    where campaign.id = registration_data.campaign_id 
    and campaign.user_id = auth.uid()
  )
);

create policy "Allow user to select own registration data"
on registration_data for select
using (
  exists (
    select 1 from campaign 
    where campaign.id = registration_data.campaign_id 
    and campaign.user_id = auth.uid()
  )
);

create policy "Allow user to update own registration data"
on registration_data for update
using (
  exists (
    select 1 from campaign 
    where campaign.id = registration_data.campaign_id 
    and campaign.user_id = auth.uid()
  )
);

create policy "Allow user to delete own registration data"
on registration_data for delete
using (
  exists (
    select 1 from campaign 
    where campaign.id = registration_data.campaign_id 
    and campaign.user_id = auth.uid()
  )
);

-- Create the petitions storage bucket (if not already created)
insert into storage.buckets (id, name, public)
values ('petitions', 'petitions', false)
on conflict (id) do nothing;

-- Create storage policies for petitions (create if they don't exist)
DO $$ 
BEGIN
    -- Upload policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow authenticated users to upload petition files'
    ) THEN
        create policy "Allow authenticated users to upload petition files"
        on storage.objects for insert
        with check (bucket_id = 'petitions' and auth.role() = 'authenticated');
    END IF;

    -- Select policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow users to view their own petition files'
    ) THEN
        create policy "Allow users to view their own petition files"
        on storage.objects for select
        using (bucket_id = 'petitions' and auth.role() = 'authenticated');
    END IF;

    -- Update policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow users to update their own petition files'
    ) THEN
        create policy "Allow users to update their own petition files"
        on storage.objects for update
        using (bucket_id = 'petitions' and auth.role() = 'authenticated');
    END IF;

    -- Delete policy
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' 
        AND schemaname = 'storage'
        AND policyname = 'Allow users to delete their own petition files'
    ) THEN
        create policy "Allow users to delete their own petition files"
        on storage.objects for delete
        using (bucket_id = 'petitions' and auth.role() = 'authenticated');
    END IF;
END $$;