-- Create unified analysis_results table for web uploads and WhatsApp
CREATE TABLE IF NOT EXISTS analysis_results (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL CHECK (source IN ('web_upload','whatsapp')),
  score NUMERIC(5,2),
  verdict TEXT,
  details_json JSONB,
  file_name TEXT,
  message_sid TEXT,
  phone_number TEXT,
  user_id TEXT,
  session_id TEXT,
  correlation_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE analysis_results IS 'Unified storage for analysis results from web uploads and WhatsApp.';
COMMENT ON COLUMN analysis_results.id IS 'Primary key.';
COMMENT ON COLUMN analysis_results.source IS 'Origin of analysis: web_upload or whatsapp.';
COMMENT ON COLUMN analysis_results.score IS 'Numeric score associated with the analysis result.';
COMMENT ON COLUMN analysis_results.verdict IS 'Short textual verdict for the analysis.';
COMMENT ON COLUMN analysis_results.details_json IS 'Arbitrary JSON details about the analysis, including metadata and previews.';
COMMENT ON COLUMN analysis_results.file_name IS 'Original filename for web uploads, if applicable.';
COMMENT ON COLUMN analysis_results.message_sid IS 'WhatsApp/Twilio message SID, if applicable.';
COMMENT ON COLUMN analysis_results.phone_number IS 'Raw phone number for WhatsApp interactions (stored unmasked).';
COMMENT ON COLUMN analysis_results.user_id IS 'Associated user identifier, if available.';
COMMENT ON COLUMN analysis_results.session_id IS 'Session identifier to group related actions.';
COMMENT ON COLUMN analysis_results.correlation_id IS 'Correlation identifier used for idempotency and deduplication across sources.';
COMMENT ON COLUMN analysis_results.created_at IS 'Timestamp when the result was recorded (UTC).';

-- Helpful indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at_desc ON analysis_results (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_results_source ON analysis_results (source);
CREATE INDEX IF NOT EXISTS idx_analysis_results_message_sid ON analysis_results (message_sid);
CREATE INDEX IF NOT EXISTS idx_analysis_results_file_name ON analysis_results (file_name);
CREATE INDEX IF NOT EXISTS idx_analysis_results_phone_number ON analysis_results (phone_number);

