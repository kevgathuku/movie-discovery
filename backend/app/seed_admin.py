"""Bootstrap the first admin user.

Run after migration rev A (users table exists), before rev B backfill:

    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=<secret> \
        python -m app.seed_admin

Refuses when an admin already exists unless --force. The password is only
ever read from the environment and never logged.
"""

import argparse
import asyncio
import os
import sys
from collections.abc import AsyncIterator, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import async_session
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.security.passwords import hash_password


async def seed_admin(
    force: bool = False,
    session_factory: Callable[[], AsyncIterator[AsyncSession]] | None = None,
) -> int:
    email = os.environ.get("ADMIN_EMAIL", "")
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not password:
        print(
            "ADMIN_EMAIL and ADMIN_PASSWORD must be set", file=sys.stderr
        )
        return 2
    if len(password) < 8:
        print("ADMIN_PASSWORD must be at least 8 characters", file=sys.stderr)
        return 2

    factory = session_factory or async_session
    async with factory() as session:
        repo = UserRepository(session)
        existing_admin = (
            await session.execute(
                select(User).where(User.role == UserRole.admin).limit(1)
            )
        ).scalar_one_or_none()
        if existing_admin is not None and not force:
            print(
                f"Admin already exists ({existing_admin.email}); "
                "use --force to create another",
                file=sys.stderr,
            )
            return 1
        if await repo.get_by_email(email) is not None:
            print(f"User already exists: {repo.normalize_email(email)}",
                  file=sys.stderr)
            return 1
        await repo.create(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )
        await session.commit()
    print(f"Admin created: {UserRepository.normalize_email(email)}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the first admin")
    parser.add_argument("--force", action="store_true",
                        help="create even if an admin exists")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(seed_admin(force=args.force)))


if __name__ == "__main__":
    main()
