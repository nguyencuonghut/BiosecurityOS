"""Reset script for development: wipe all data, re-run migrations, re-seed.

Usage (inside backend container):
    python -m app.reset_data          # Reset DB + MinIO
    python -m app.reset_data --db     # Reset DB only
    python -m app.reset_data --minio  # Reset MinIO only

Or via Makefile:
    make reset-data
"""

import argparse
import asyncio
import subprocess
import sys

from miniopy_async import Minio
from sqlalchemy import text

from app.config import settings
from app.database import async_session_factory


async def reset_database() -> None:
    """Drop all tables in biosec schema, re-run Alembic migrations, re-seed users."""
    print("\n══════════════════════════════════════════")
    print("  DATABASE RESET")
    print("══════════════════════════════════════════")

    # --- Step 1: Drop all tables ---
    print("\n[1/3] Dropping all tables in 'biosec' schema...")
    async with async_session_factory() as db:
        # Drop all tables via CASCADE, keep the schema itself
        await db.execute(text("DROP SCHEMA IF EXISTS biosec CASCADE"))
        await db.execute(text("CREATE SCHEMA biosec"))
        await db.execute(text("COMMENT ON SCHEMA biosec IS 'Schema nghiệp vụ chính cho BIOSECURITY OS 2026'"))
        await db.commit()
    print("   ✓ All tables dropped")

    # --- Step 2: Re-run Alembic migrations (via subprocess to avoid nested event loop) ---
    print("\n[2/3] Running Alembic migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"   ✗ Alembic failed:\n{result.stderr}")
        sys.exit(1)
    print("   ✓ Migrations applied")

    # --- Step 3: Re-seed all sample data ---
    print("\n[3/3] Seeding all sample data...")
    from app.seed import seed_all
    await seed_all()

    print("\n✓ Database reset complete!")


async def reset_minio() -> None:
    """Remove all objects from the MinIO bucket."""
    print("\n══════════════════════════════════════════")
    print("  MINIO RESET")
    print("══════════════════════════════════════════")

    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )

    bucket = settings.MINIO_BUCKET

    # Check if bucket exists
    if not await client.bucket_exists(bucket):
        print(f"   Bucket '{bucket}' does not exist — nothing to clean.")
        print("\n✓ MinIO reset complete!")
        return

    # List and delete all objects
    print(f"\n[1/1] Removing all objects from bucket '{bucket}'...")
    count = 0
    objects = client.list_objects(bucket, recursive=True)
    async for obj in objects:
        await client.remove_object(bucket, obj.object_name)
        count += 1
        if count % 50 == 0:
            print(f"   ... deleted {count} objects")

    # Close the internal aiohttp session to avoid warnings
    if hasattr(client, '_http') and hasattr(client._http, '_session'):
        session = client._http._session
        if session and not session.closed:
            await session.close()

    print(f"   ✓ Deleted {count} object(s)")
    print("\n✓ MinIO reset complete!")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Reset development data (DB + MinIO)")
    parser.add_argument("--db", action="store_true", help="Reset database only")
    parser.add_argument("--minio", action="store_true", help="Reset MinIO only")
    args = parser.parse_args()

    # If no flags → reset both
    reset_both = not args.db and not args.minio

    print("╔══════════════════════════════════════════╗")
    print("║   BIOSECURITY OS — DEV DATA RESET        ║")
    print("╚══════════════════════════════════════════╝")

    if settings.ENVIRONMENT != "development":
        print(f"\n✗ ENVIRONMENT={settings.ENVIRONMENT}. This script only runs in 'development'.")
        sys.exit(1)

    if reset_both or args.minio:
        await reset_minio()

    if reset_both or args.db:
        await reset_database()

    print("\n══════════════════════════════════════════")
    print("  ALL DONE — fresh environment ready!")
    print("══════════════════════════════════════════\n")


if __name__ == "__main__":
    asyncio.run(main())
