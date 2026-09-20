-- Run once per environment from the Databricks SQL editor.
-- Parameter: env = dev | test | prod
CREATE CATALOG IF NOT EXISTS vendor_drop_${env};
USE CATALOG vendor_drop_${env};

CREATE SCHEMA IF NOT EXISTS landing;   -- volumes only, no tables
CREATE SCHEMA IF NOT EXISTS bronze;    -- raw rows exactly as received
CREATE SCHEMA IF NOT EXISTS silver;    -- typed, validated, deduplicated + quarantine
CREATE SCHEMA IF NOT EXISTS gold;      -- aggregates for dashboards
CREATE SCHEMA IF NOT EXISTS ops;       -- file registry, drift log, run history

CREATE VOLUME IF NOT EXISTS landing.inbound;      -- vendors drop files here
CREATE VOLUME IF NOT EXISTS landing.archive;      -- processed files move here
CREATE VOLUME IF NOT EXISTS landing.checkpoints;  -- Auto Loader state
