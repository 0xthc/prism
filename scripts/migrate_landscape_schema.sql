-- Migration: add enriched fields to landscape_deals
-- Run this once in Supabase SQL editor (Dashboard → SQL Editor)

ALTER TABLE landscape_deals
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS exit_type text,
  ADD COLUMN IF NOT EXISTS exit_acquirer text,
  ADD COLUMN IF NOT EXISTS exit_date text,
  ADD COLUMN IF NOT EXISTS investment_date text,
  ADD COLUMN IF NOT EXISTS source_url text,
  ADD COLUMN IF NOT EXISTS description text,
  ADD COLUMN IF NOT EXISTS data_source text DEFAULT 'manual';

-- status: 'active' | 'exited' | 'shutdown' | 'unknown'
-- exit_type: 'acquired' | 'ipo' | 'shutdown' | null
-- data_source: 'scraped' | 'manual' | 'rss'
