import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig

from demon_cry.__main__ import app
from demon_cry.config import (
    Config,
    read_value,
    resolve_config_path,
    write_value,
    _infer_value,
)

banner = r"""
     _
  __| | ___ _ __ ___   ___  _ __     ___ _ __ _   _    ___ ___  _ __ ___
 / _` |/ _ \ '_ ` _ \ / _ \| '_ \   / __| '__| | | |  / __/ _ \| '__/ _ \
| (_| |  __/ | | | | | (_) | | | | | (__| |  | |_| | | (_| (_) | | |  __/
 \__,_|\___|_| |_| |_|\___/|_| |_|  \___|_|   \__, |  \___\___/|_|  \___|
                                              |___/
"""


def _build_alembic_config() -> AlembicConfig:
    ini_path = Path(__file__).parent / "alembic.ini"
    return AlembicConfig(str(ini_path))


def _migrate_command(args: argparse.Namespace) -> int:
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


def _config_command(args: argparse.Namespace) -> int:
    if args.config_action == "path":
        print(resolve_config_path())
        return 0
    if args.config_action == "get":
        try:
            print(read_value(args.key))
        except (FileNotFoundError, KeyError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0
    if args.config_action == "set":
        path = write_value(args.key, _infer_value(args.value))
        print(f"Set {args.key} -> {path}")
        return 0
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demon-cry",
        description="Run the Demon Cry OSINT agent API server.",
    )
    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser("config", help="Read/write config.toml")
    config_sub = config_parser.add_subparsers(dest="config_action", required=True)
    config_set = config_sub.add_parser("set", help="Set a config value")
    config_set.add_argument("key", help="Key, e.g. base_url or db.link")
    config_set.add_argument("value", help="Value (type inferred: int/bool/string)")
    config_get = config_sub.add_parser("get", help="Print a config value")
    config_get.add_argument("key", help="Key, e.g. base_url or db.link")
    config_sub.add_parser("path", help="Print the resolved config path")

    migrate_parser = subparsers.add_parser(
        "migrate", help="Run database migrations (Alembic)"
    )
    migrate_sub = migrate_parser.add_subparsers(dest="migrate_action", required=True)
    upgrade_parser = migrate_sub.add_parser("upgrade", help="Upgrade to a revision")
    upgrade_parser.add_argument(
        "revision", nargs="?", default="head", help="Target revision (default: head)"
    )
    downgrade_parser = migrate_sub.add_parser(
        "downgrade", help="Downgrade to a revision"
    )
    downgrade_parser.add_argument(
        "revision", nargs="?", default="-1", help="Target revision (default: -1)"
    )
    migrate_sub.add_parser("current", help="Show current revision")
    migrate_sub.add_parser("history", help="Show migration history")

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the startup banner.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "command", None) == "config":
        raise SystemExit(_config_command(args))

    if getattr(args, "command", None) == "migrate":
        raise SystemExit(_migrate_command(args))

    import uvicorn

    config = Config.load()

    if not args.no_banner:
        print(banner)

    uvicorn.run(app, host=config.server.host, port=config.server.port)


if __name__ == "__main__":
    main()
