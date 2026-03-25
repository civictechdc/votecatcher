"""Purge old campaign data, keeping only the N most recent campaigns.

Usage:
    python scripts/purge_old_campaigns.py [--keep N] [--dry-run]

Options:
    --keep N    Number of campaigns to keep [default: 10]
    --dry-run   Show what would be deleted without actually deleting
"""

import argparse
import sqlite3
from pathlib import Path


def get_db_path() -> Path:
	return Path(__file__).parent.parent / "dev.db"


def purge_old_campaigns(keep: int = 10, dry_run: bool = False) -> None:
	db_path = get_db_path()
	if not db_path.exists():
		print(f"Database not found: {db_path}")
		return

	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	cursor.execute(
		f"""
        SELECT id, unique_name, created_at
        FROM campaigns
        ORDER BY created_at DESC
        LIMIT {keep}
    """
	)
	keep_campaigns = cursor.fetchall()
	keep_ids = [c[0] for c in keep_campaigns]

	print(f"\n=== Campaigns to KEEP ({len(keep_ids)}) ===")
	for c in keep_campaigns:
		print(f"  - {c[0]}: {c[1]} ({c[2]})")

	cursor.execute("SELECT COUNT(*) FROM campaigns")
	total = cursor.fetchone()[0]

	if total <= keep:
		print(f"\nOnly {total} campaigns exist, nothing to purge.")
		conn.close()
		return

	placeholders = ",".join("?" * len(keep_ids))
	not_in_clause = f"NOT IN ({placeholders})"

	counts = {}

	cursor.execute(
		f"""
        SELECT COUNT(*) FROM match_results
        WHERE matcher_job_id IN (SELECT id FROM matcher_jobs WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	counts["match_results"] = cursor.fetchone()[0]

	cursor.execute(
		f"SELECT COUNT(*) FROM matcher_jobs WHERE campaign_id {not_in_clause}", keep_ids
	)
	counts["matcher_jobs"] = cursor.fetchone()[0]

	cursor.execute(
		f"SELECT COUNT(*) FROM petition_scans WHERE campaign_id {not_in_clause}",
		keep_ids,
	)
	counts["petition_scans"] = cursor.fetchone()[0]

	cursor.execute(
		f"""
        SELECT COUNT(*) FROM petition_crops
        WHERE scan_id IN (SELECT id FROM petition_scans WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	counts["petition_crops"] = cursor.fetchone()[0]

	cursor.execute(
		f"""
        SELECT COUNT(*) FROM ocr_results
        WHERE crop_id IN (
            SELECT pc.id FROM petition_crops pc
            JOIN petition_scans ps ON pc.scan_id = ps.id
            WHERE ps.campaign_id {not_in_clause}
        )
    """,
		keep_ids,
	)
	counts["ocr_results"] = cursor.fetchone()[0]

	cursor.execute(
		f"""
        SELECT COUNT(*) FROM ocr_jobs
        WHERE matcher_job_id IN (SELECT id FROM matcher_jobs WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	counts["ocr_jobs"] = cursor.fetchone()[0]

	cursor.execute(f"SELECT COUNT(*) FROM campaigns WHERE id {not_in_clause}", keep_ids)
	counts["campaigns"] = cursor.fetchone()[0]

	print("\n=== Data to DELETE ===")
	for table, count in counts.items():
		print(f"  - {table}: {count} rows")

	total_to_delete = sum(counts.values())
	print(f"\n  Total: {total_to_delete} rows")

	if dry_run:
		print("\n=== DRY RUN - No changes made ===")
		conn.close()
		return

	print("\n=== PURGING ===")

	cursor.execute(
		f"""
        DELETE FROM match_results
        WHERE matcher_job_id IN (SELECT id FROM matcher_jobs WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	print(f"  - Deleted from match_results: {cursor.rowcount} rows")

	cursor.execute(
		f"""
        DELETE FROM ocr_results
        WHERE crop_id IN (
            SELECT pc.id FROM petition_crops pc
            JOIN petition_scans ps ON pc.scan_id = ps.id
            WHERE ps.campaign_id {not_in_clause}
        )
    """,
		keep_ids,
	)
	print(f"  - Deleted from ocr_results: {cursor.rowcount} rows")

	cursor.execute(
		f"""
        DELETE FROM ocr_jobs
        WHERE matcher_job_id IN (SELECT id FROM matcher_jobs WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	print(f"  - Deleted from ocr_jobs: {cursor.rowcount} rows")

	cursor.execute(
		f"DELETE FROM matcher_jobs WHERE campaign_id {not_in_clause}", keep_ids
	)
	print(f"  - Deleted from matcher_jobs: {cursor.rowcount} rows")

	cursor.execute(
		f"""
        DELETE FROM petition_crops
        WHERE scan_id IN (SELECT id FROM petition_scans WHERE campaign_id {not_in_clause})
    """,
		keep_ids,
	)
	print(f"  - Deleted from petition_crops: {cursor.rowcount} rows")

	cursor.execute(
		f"DELETE FROM petition_scans WHERE campaign_id {not_in_clause}", keep_ids
	)
	print(f"  - Deleted from petition_scans: {cursor.rowcount} rows")

	cursor.execute(f"DELETE FROM campaigns WHERE id {not_in_clause}", keep_ids)
	print(f"  - Deleted from campaigns: {cursor.rowcount} rows")

	conn.commit()

	cursor.execute("VACUUM")
	print("\n=== Database vacuumed ===")

	print("\n=== Final row counts ===")
	for table in [
		"campaigns",
		"petition_scans",
		"petition_crops",
		"matcher_jobs",
		"ocr_jobs",
		"ocr_results",
		"match_results",
	]:
		cursor.execute(f"SELECT COUNT(*) FROM {table}")
		count = cursor.fetchone()[0]
		print(f"  - {table}: {count} rows")

	conn.close()
	print("\n=== DONE ===")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Purge old campaign data")
	parser.add_argument(
		"--keep", type=int, default=10, help="Number of campaigns to keep"
	)
	parser.add_argument(
		"--dry-run", action="store_true", help="Show what would be deleted"
	)
	args = parser.parse_args()

	purge_old_campaigns(keep=args.keep, dry_run=args.dry_run)
