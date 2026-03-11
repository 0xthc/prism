-- Prism Precognition table
-- Run at: https://supabase.com/dashboard/project/datqjbnetudvqjsxjczl/sql/new

CREATE TABLE IF NOT EXISTS consumer_founders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_name TEXT NOT NULL,
  founder_name TEXT,
  category TEXT,
  sub_category TEXT,
  stage TEXT,           -- 'pre-raise', 'raising', 'seed', 'series-a'
  score INTEGER,        -- 0-100
  accelerator TEXT,     -- e.g. 'Chobani Incubator', 'SKS Accelerator'
  cohort TEXT,          -- e.g. 'W26', '2025'
  why_surfaced TEXT,    -- plain English explanation
  signals JSONB,        -- array of {label, detail} signal objects
  source TEXT,
  source_url TEXT,
  location TEXT,
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(brand_name)
);

ALTER TABLE consumer_founders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read" ON consumer_founders FOR SELECT USING (true);
