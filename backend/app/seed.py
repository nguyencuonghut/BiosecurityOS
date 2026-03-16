"""Seed script for development: creates sample users for every role."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AppRole, AppUser, AppUserCredential, UserRole
from app.auth.security import hash_password
from app.database import async_session_factory

# (username, full_name, email, role_code)
SEED_USERS = [
    ("admin", "System Administrator", "admin@biosec.local", "SYSTEM_ADMIN"),
    ("region_mgr", "Nguyễn Văn Vùng", "region_mgr@biosec.local", "REGION_MANAGER"),
    ("farm_mgr", "Trần Thị Trại", "farm_mgr@biosec.local", "FARM_MANAGER"),
    ("expert", "Lê Văn Chuyên", "expert@biosec.local", "BIOSEC_EXPERT"),
    ("auditor", "Phạm Thị Kiểm", "auditor@biosec.local", "AUDITOR"),
    ("viewer", "Hoàng Văn Xem", "viewer@biosec.local", "VIEWER"),
]

DEFAULT_PASSWORD = "Admin@2026"


async def seed_users() -> None:
    async with async_session_factory() as db:
        for username, full_name, email, role_code in SEED_USERS:
            # Skip if user already exists
            result = await db.execute(select(AppUser).where(AppUser.username == username))
            if result.scalar_one_or_none():
                print(f"User '{username}' already exists, skipping.")
                continue

            user = AppUser(
                username=username,
                full_name=full_name,
                email=email,
                status="active",
            )
            db.add(user)
            await db.flush()

            cred = AppUserCredential(
                user_id=user.id,
                password_hash=hash_password(DEFAULT_PASSWORD),
            )
            db.add(cred)

            # Assign role
            role_result = await db.execute(select(AppRole).where(AppRole.code == role_code))
            role = role_result.scalar_one_or_none()
            if role:
                db.add(UserRole(user_id=user.id, role_id=role.id))

            print(f"Created user: {username} / {role_code} (id={user.id})")

        await db.commit()


async def main():
    await seed_users()


if __name__ == "__main__":
    asyncio.run(main())
