-- Run this in your Supabase SQL editor to set up the businesses table.
-- Safe to re-run. Mirrors the SQLite schema in scraper/db.py.

create table if not exists businesses (
  id                  bigint generated always as identity primary key,
  place_id            text unique not null,
  name                text not null,
  address             text,
  phone               text,
  website             text,
  rating              numeric,
  review_count        integer,
  category            text,
  hours_json          text,
  photo_refs          text,
  lat                 numeric,
  lng                 numeric,
  slug                text,
  owner_name          text,
  owner_email         text,
  status              text default 'scraped',
  demo_url            text,
  outreach_status     text default 'new',
  outreach_sent_at    text,
  outreach_channel    text,
  outreach_subject    text,
  outreach_body_id    text,
  outreach_opened_at  text,
  outreach_replied_at text,
  closed_amount       numeric,
  notes               text,
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

create index if not exists businesses_status_idx on businesses (status);
create index if not exists businesses_outreach_status_idx on businesses (outreach_status);
