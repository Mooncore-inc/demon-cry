import argparse
import asyncio
import logging
import sys
from os import environ

from demon_cry.__main__ import app
from demon_cry.config import (
    Config,
    DEFAULTS,
    get_config_value,
    init_defaults,
    set_config_value,
)

banner = r"""
      _
   __| | ___ _ __ ___   ___  _ __     ___ _ __ _   _    ___ ___  _ __ ___
  / _` |/ _ \ '_ ` _ \ / _ \| '_ \   / __| '__| | | |  / __/ _ \| '__/ _ \
 | (_| |  __/ | | | | | (_) | | | | | (__| |  | |_| | | (_| (_) | | |  __/
  \__,_|\___|_| |_| |_|\___/|_| |_|  \___|_|   \__, |  \___\___/|_|  \___|
                                                |___/
"""


def _build_alembic_config():
    from pathlib import Path
    from alembic.config import Config as AlembicConfig

    ini_path = Path(__file__).parent / "alembic.ini"
    return AlembicConfig(str(ini_path))


def _migrate_command(args: argparse.Namespace) -> int:
    from alembic import command

    cfg = _build_alembic_config()
    action = args.migrate_action
    if action == "upgrade":
        command.upgrade(cfg, args.revision or "head")
    elif action == "downgrade":
        command.downgrade(cfg, args.revision or "-1")
    elif action == "current":
        command.current(cfg)
    elif action == "history":
        command.history(cfg)
    else:
        return 2
    return 0


async def _user_create(username: str, is_admin: bool) -> int:
    from uuid import uuid4
    from demon_cry.database.engine import async_session_factory
    from demon_cry.database.repositories.user import UserRepository

    api_key = str(uuid4())
    async with async_session_factory() as session:
        repo = UserRepository(session)
        existing = await repo.get(username=username)
        if existing:
            print(f"User '{username}' already exists", file=sys.stderr)
            return 1
        await repo.create(username=username, credentials=api_key, is_admin=is_admin)

    print(f"User '{username}' created")
    print(f"API key: {api_key}")
    print("Save this key — it won't be shown again.")
    return 0


def _user_command(args: argparse.Namespace) -> int:
    if args.user_action == "create":
        return asyncio.run(_user_create(args.username, args.admin))
    return 2


async def _config_get(key: str) -> int:
    try:
        await init_defaults()
        value = await get_config_value(key)
        print(value)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


async def _config_set(key: str, value: str) -> int:
    try:
        await set_config_value(key, value)
        print(f"Set {key}")
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _config_command(args: argparse.Namespace) -> int:
    if args.config_action == "get":
        return asyncio.run(_config_get(args.key))
    if args.config_action == "set":
        return asyncio.run(_config_set(args.key, args.value))
    if args.config_action == "list":
        for key in DEFAULTS:
            print(key)
        return 0
    if args.config_action == "defaults":
        for key, value in DEFAULTS.items():
            print(f"{key} = {value}")
        return 0
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demon-cry",
        description="Run the Demon Cry OSINT agent API server.",
    )
    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser("config", help="Read/write config")
    config_sub = config_parser.add_subparsers(dest="config_action", required=True)
    config_set = config_sub.add_parser("set", help="Set a config value")
    config_set.add_argument("key", help="Key, e.g. base_url or model")
    config_set.add_argument("value", help="Value")
    config_get = config_sub.add_parser("get", help="Print a config value")
    config_get.add_argument("key", help="Key, e.g. base_url or model")
    config_sub.add_parser("list", help="List all config keys")
    config_sub.add_parser("defaults", help="Show default values")

    migrate_parser = subparsers.add_parser(
        "migrate", help="Run database migrations (Alembic)"
    )
    migrate_sub = migrate_parser.add_subparsers(dest="migrate_action", required=True)
    upgrade_parser = migrate_sub.add_parser("upgrade", help="Upgrade to a revision")
    upgrade_parser.add_argument(
        "revision", nargs="?", default="head", help="Target revision (default: head)"
    )
    downgrade_parser = migrate_sub.add_parser("downgrade", help="Downgrade to a revision")
    downgrade_parser.add_argument(
        "revision", nargs="?", default="-1", help="Target revision (default: -1)"
    )
    migrate_sub.add_parser("current", help="Show current revision")
    migrate_sub.add_parser("history", help="Show migration history")

    user_parser = subparsers.add_parser("user", help="Manage users")
    user_sub = user_parser.add_subparsers(dest="user_action", required=True)
    user_create = user_sub.add_parser("create", help="Create a new user")
    user_create.add_argument("username", help="Username")
    user_create.add_argument(
        "--admin", action="store_true", help="Create as admin"
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the startup banner.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(funcName)s@%(filename)s:%(lineno)d) -> %(message)s",
        filename=environ.get("DEMON_CRY_LOG") or None,
        filemode="a",
    )

    if getattr(args, "command", None) == "config":
        raise SystemExit(_config_command(args))

    if getattr(args, "command", None) == "migrate":
        raise SystemExit(_migrate_command(args))

    if getattr(args, "command", None) == "user":
        raise SystemExit(_user_command(args))

    import uvicorn

    config = asyncio.run(Config.load())

    if not args.no_banner:
        print(banner)

    uvicorn.run(app, host=config.server_host, port=config.server_port)


if __name__ == "__main__":
    main()
