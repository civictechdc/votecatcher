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

-- Create the petitions storage bucket (if not already created)
insert into storage.buckets (id, name, public)
values ('petitions', 'petitions', false)
on conflict (id) do nothing;

-- Allow authenticated users to upload petition files
create policy "Allow authenticated users to upload petition files"
on storage.objects for insert
with check (bucket_id = 'petitions' and auth.role() = 'authenticated');

-- Allow users to view their own petition files
create policy "Allow users to view their own petition files"
on storage.objects for select
using (bucket_id = 'petitions' and auth.role() = 'authenticated');

-- Allow users to update their own petition files
create policy "Allow users to update their own petition files"
on storage.objects for update
using (bucket_id = 'petitions' and auth.role() = 'authenticated');

-- Allow users to delete their own petition files
create policy "Allow users to delete their own petition files"
on storage.objects for delete
using (bucket_id = 'petitions' and auth.role() = 'authenticated');