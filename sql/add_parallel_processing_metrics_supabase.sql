-- Migration: Add parallel processing metrics to performance_metrics table
-- Run this in Supabase SQL editor

-- Add parallel processing fields
ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS is_parallel BOOLEAN DEFAULT FALSE;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS parallel_slot_count INTEGER;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS sequential_time_ms REAL;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS rate_limit_errors INTEGER DEFAULT 0;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS concurrency_level INTEGER;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS tpm_usage INTEGER;

ALTER TABLE performance_metrics 
ADD COLUMN IF NOT EXISTS rpm_usage INTEGER;

-- Add comments (PostgreSQL specific)
COMMENT ON COLUMN performance_metrics.is_parallel IS 'Whether operation was processed in parallel';
COMMENT ON COLUMN performance_metrics.parallel_slot_count IS 'Number of slots processed in parallel';
COMMENT ON COLUMN performance_metrics.sequential_time_ms IS 'Estimated time if processed sequentially';
COMMENT ON COLUMN performance_metrics.rate_limit_errors IS 'Number of rate limit errors encountered';
COMMENT ON COLUMN performance_metrics.concurrency_level IS 'Actual concurrency level used';
COMMENT ON COLUMN performance_metrics.tpm_usage IS 'Tokens per minute usage at time of request';
COMMENT ON COLUMN performance_metrics.rpm_usage IS 'Requests per minute usage at time of request';

-- Create index for parallel processing queries
CREATE INDEX IF NOT EXISTS idx_performance_metrics_is_parallel 
ON performance_metrics(is_parallel, plan_id);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_parallel_slot_count 
ON performance_metrics(parallel_slot_count) 
WHERE parallel_slot_count IS NOT NULL;
