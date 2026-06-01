CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE raw_signals (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  niche         TEXT NOT NULL CHECK (niche IN ('football', 'sports_toys', '3d_printed_toys')),
  source        TEXT NOT NULL,
  source_type   TEXT NOT NULL CHECK (source_type IN ('trends', 'news', 'reddit', 'scrape')),
  external_id   TEXT,
  title         TEXT,
  url           TEXT,
  raw_payload   JSONB NOT NULL,
  fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_raw_signals_niche_fetched ON raw_signals(niche, fetched_at DESC);
CREATE UNIQUE INDEX idx_raw_signals_dedup ON raw_signals(source, external_id) WHERE external_id IS NOT NULL;

CREATE TABLE daily_reports (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  report_date   DATE NOT NULL UNIQUE,
  status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','success','partial','failed')),
  niches        JSONB NOT NULL DEFAULT '{}',
  markdown      TEXT,
  signals_used  INTEGER DEFAULT 0,
  llm_tokens    INTEGER DEFAULT 0,
  duration_ms   INTEGER,
  errors        JSONB DEFAULT '[]',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date DESC);

CREATE TABLE chat_messages (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('user','assistant','tool')),
  content         TEXT NOT NULL,
  tool_calls      JSONB,
  citations       JSONB,
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chat_messages_conv ON chat_messages(conversation_id, created_at);

CREATE TABLE cron_runs (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_name    TEXT NOT NULL,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status      TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
  error_msg   TEXT,
  metadata    JSONB
);
CREATE INDEX idx_cron_runs_job_started ON cron_runs(job_name, started_at DESC);

CREATE TABLE sources_health (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source       TEXT NOT NULL,
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  success      BOOLEAN NOT NULL,
  signals_count INTEGER DEFAULT 0,
  error_msg    TEXT,
  duration_ms  INTEGER
);
CREATE INDEX idx_sources_health_source_time ON sources_health(source, attempted_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER daily_reports_updated_at BEFORE UPDATE ON daily_reports
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
