# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

import secrets
import base64
from pathlib import Path
import argparse
import sys

def main(path: Path) -> None:
    # Ensure parent directories exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate 64 random bytes and base64-encode
    key = base64.b64encode(secrets.token_bytes(64)).decode("utf-8")

    # Write to file
    path.write_text(key)
    print(f"Secret key written to: {path.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a base64-encoded secret key and save it to a file."
    )
    parser.add_argument(
        "--path", "-p",
        type=Path,
        default=Path(".secret"),
        help="Path to save the secret file (default: .secret)"
    )
    args = parser.parse_args()

    try:
        main(args.path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
