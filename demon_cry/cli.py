import argparse

from demon_cry.__main__ import app


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
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
