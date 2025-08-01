-- Create enum for campaign status
create type campaign_status as enum ('inactive', 'active');

-- Add trigger function for updated_at columns
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Create campaign table with audit fields
create table public.campaign (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  name character varying(255) not null,
  description text null,
  year integer not null,
  status campaign_status default 'inactive',
  is_active boolean default true,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  constraint campaign_name_length check (char_length(name) >= 3),
  constraint campaign_year_range check (year >= 2020 and year <= 2030)
);

-- Enable RLS
alter table public.campaign enable row level security;

-- Policies for campaign table
create policy "Allow user to insert own campaigns"
on public.campaign for insert
with check (auth.uid() = user_id);

create policy "Allow user to select own campaigns"
on public.campaign for select
using (auth.uid() = user_id and is_active = true);

create policy "Allow user to update own campaigns"
on public.campaign for update
using (auth.uid() = user_id);

create policy "Allow user to delete own campaigns"
on public.campaign for delete
using (auth.uid() = user_id);

-- Create indexes for better performance
create index campaign_user_id_idx on public.campaign (user_id);
create index campaign_created_at_idx on public.campaign (created_at);
create index campaign_status_idx on public.campaign (status);
create index campaign_year_idx on public.campaign (year);

-- Create trigger for updated_at column (reuses existing function)
create trigger update_campaign_updated_at
  before update on public.campaign
  for each row execute function update_updated_at_column();

-- Function to ensure only one active campaign per user
create or replace function ensure_single_active_campaign()
returns trigger as $$
begin
  -- If we're setting a campaign to active, deactivate all other campaigns for this user
  if new.status = 'active' then
    update public.campaign 
    set status = 'inactive' 
    where user_id = new.user_id 
    and id != new.id 
    and status = 'active';
  end if;
  return new;
end;
$$ language plpgsql;

-- Create trigger to enforce single active campaign
create trigger enforce_single_active_campaign
  before insert or update on public.campaign
  for each row execute function ensure_single_active_campaign(); 