-- Create enum for providers
create type provider_enum as enum ('OPENAI_API_KEY', 'MISTRAL_API_KEY', 'GEMINI_API_KEY');

-- Create table with audit fields
create table api_keys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  provider provider_enum not null,
  api_key text not null,
  is_active boolean default true,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique (user_id, provider)
);

-- Enable RLS
alter table api_keys enable row level security;

-- Policies for api_keys table
create policy "Allow user to insert own API keys"
on api_keys for insert
with check (auth.uid() = user_id);

create policy "Allow user to select own API keys"
on api_keys for select
using (auth.uid() = user_id and is_active = true);

create policy "Allow user to update own API keys"
on api_keys for update
using (auth.uid() = user_id);

create policy "Allow user to delete own API keys"
on api_keys for delete
using (auth.uid() = user_id);

-- Create usage tracking table
create table api_key_usage (
  id uuid primary key default gen_random_uuid(),
  api_key_id uuid references api_keys not null,
  usage_count integer default 0,
  last_used_at timestamp with time zone,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Enable RLS for usage table
alter table api_key_usage enable row level security;

-- Policies for api_key_usage table
create policy "Allow user to view own API key usage"
on api_key_usage for select
using (
  exists (
    select 1 from api_keys 
    where api_keys.id = api_key_usage.api_key_id 
    and api_keys.user_id = auth.uid()
  )
);

create policy "Allow user to insert own API key usage"
on api_key_usage for insert
with check (
  exists (
    select 1 from api_keys 
    where api_keys.id = api_key_usage.api_key_id 
    and api_keys.user_id = auth.uid()
  )
);

create policy "Allow user to update own API key usage"
on api_key_usage for update
using (
  exists (
    select 1 from api_keys 
    where api_keys.id = api_key_usage.api_key_id 
    and api_keys.user_id = auth.uid()
  )
);

-- Note: update_updated_at_column() function is defined in campaign-schema.sql

-- Create triggers for updated_at
create trigger update_api_keys_updated_at
  before update on api_keys
  for each row execute function update_updated_at_column();

create trigger update_api_key_usage_updated_at
  before update on api_key_usage
  for each row execute function update_updated_at_column(); 