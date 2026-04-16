-- Add indexes on FK columns for match_results and ocr_results
-- Required for SQL-level pagination performance (EPIC-3)

CREATE INDEX IF NOT EXISTS ix_match_results_ocr_result_id ON match_results (ocr_result_id);
CREATE INDEX IF NOT EXISTS ix_match_results_matcher_job_id ON match_results (matcher_job_id);
CREATE INDEX IF NOT EXISTS ix_match_results_voter_id ON match_results (voter_id);

CREATE INDEX IF NOT EXISTS ix_ocr_results_crop_id ON ocr_results (crop_id);
CREATE INDEX IF NOT EXISTS ix_ocr_results_ocr_job_id ON ocr_results (ocr_job_id);
