-- Prism Database Schema
-- Run this in the Supabase SQL editor at:
-- https://supabase.com/dashboard/project/datqjbnetudvqjsxjczl/sql

-- Fund raises with niche consumer theses
CREATE TABLE IF NOT EXISTS fund_raises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fund_name TEXT NOT NULL,
  gp_name TEXT,
  fund_size_m INTEGER,         -- in millions USD
  check_min_k INTEGER,         -- min check size in thousands USD
  check_max_m INTEGER,         -- max check size in millions USD
  thesis TEXT,                 -- 1-2 sentence thesis
  categories TEXT[],           -- consumer categories validated
  lp_signal TEXT,              -- notable LPs (signal of what strategics believe)
  watch TEXT,                  -- what to watch as a result
  announced_date DATE,
  source_url TEXT,
  source TEXT,                 -- e.g. 'techcrunch', 'axios', 'manual'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(fund_name, announced_date)
);

-- Early consumer brand signals
CREATE TABLE IF NOT EXISTS brand_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_name TEXT NOT NULL,
  category TEXT,               -- e.g. 'food & beverage', 'beauty', 'wellness'
  sub_category TEXT,           -- e.g. 'functional beverage', 'skincare'
  stage TEXT,                  -- 'pre-launch', 'launch', 'early-traction', 'seed-raised'
  what TEXT,                   -- what are they doing
  why_now TEXT,                -- timing signal
  signal_type TEXT,            -- 'product_hunt', 'press', 'rss', 'manual'
  source_url TEXT,
  founder TEXT,
  location TEXT,
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(brand_name, detected_at::DATE)
);

-- Trend/ingredient shifts
CREATE TABLE IF NOT EXISTS trend_shifts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trend_name TEXT NOT NULL,    -- e.g. 'bakuchiol', 'beet gummies', 'staycation'
  category TEXT,               -- 'ingredient', 'usage_paradigm', 'format'
  shift_from TEXT,             -- what it replaces (e.g. 'retinol')
  shift_to TEXT,               -- the new thing
  stage TEXT,                  -- 'emerging', 'accelerating', 'peaking', 'mainstream'
  signal TEXT,                 -- what signals this shift
  consumer TEXT,               -- who the consumer is
  momentum INTEGER,            -- 0-100 score
  source TEXT,                 -- 'exploding_topics', 'google_trends', 'manual', 'rss'
  source_url TEXT,
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(trend_name, detected_at::DATE)
);

-- Enable row level security (read-only for anon)
ALTER TABLE fund_raises ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trend_shifts ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Public read" ON fund_raises FOR SELECT USING (true);
CREATE POLICY "Public read" ON brand_signals FOR SELECT USING (true);
CREATE POLICY "Public read" ON trend_shifts FOR SELECT USING (true);
