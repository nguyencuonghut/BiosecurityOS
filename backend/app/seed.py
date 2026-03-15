"""Seed script for development: creates an admin user + assigns SYSTEM_ADMIN role."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AppRole, AppUser, AppUserCredential, UserRole
from app.auth.security import hash_password
from app.database import async_session_factory


async def seed_admin() -> None:
    async with async_session_factory() as db:
        # Check if admin already exists
        result = await db.execute(select(AppUser).where(AppUser.username == "admin"))
        if result.scalar_one_or_none():
            print("Admin user already exists, skipping.")
            return

        user = AppUser(
            username="admin",
            full_name="System Administrator",
            email="admin@biosec.local",
            status="active",
        )
        db.add(user)
        await db.flush()

        cred = AppUserCredential(
            user_id=user.id,
            password_hash=hash_password("Admin@2026"),
        )
        db.add(cred)

        # Find SYSTEM_ADMIN role
        role_result = await db.execute(select(AppRole).where(AppRole.code == "SYSTEM_ADMIN"))
        admin_role = role_result.scalar_one_or_none()
        if admin_role:
            ur = UserRole(user_id=user.id, role_id=admin_role.id)
            db.add(ur)

        await db.commit()
        print(f"Created admin user: {user.username} (id={user.id})")


async def main():
    await seed_admin()


if __name__ == "__main__":
    asyncio.run(main())
