import argparse

from demon_cry.__main__ import app

banner = r"""
     _
  __| | ___ _ __ ___   ___  _ __     ___ _ __ _   _    ___ ___  _ __ ___
 / _` |/ _ \ '_ ` _ \ / _ \| '_ \   / __| '__| | | |  / __/ _ \| '__/ _ \
| (_| |  __/ | | | | | (_) | | | | | (__| |  | |_| | | (_| (_) | | |  __/
 \__,_|\___|_| |_| |_|\___/|_| |_|  \___|_|   \__, |  \___\___/|_|  \___|
                                              |___/
"""

def main():
    parser = argparse.ArgumentParser(
        prog="demon-cry",
        description="Run the Demon Cry OSINT agent API server.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host/address to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the startup banner.",
    )
    args = parser.parse_args()

    import uvicorn

    if not args.no_banner:
        print(banner)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
