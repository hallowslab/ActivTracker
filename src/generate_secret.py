# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

import argparse
import base64
import secrets
import sys
from pathlib import Path


def main(path: Path) -> None:
    # Ensure parent directories exist
    """
    Generate a cryptographically strong 64-byte secret key, base64-encode it, and write it to the given file path.
    
    The function ensures the file's parent directories exist, writes the encoded key to the file, and prints the resolved path to confirm where the key was written.
    
    Parameters:
        path (Path): Filesystem path where the base64-encoded secret key will be saved.
    """
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
        "--path",
        "-p",
        type=Path,
        default=Path(".secret"),
        help="Path to save the secret file (default: .secret)",
    )
    args = parser.parse_args()

    try:
        main(args.path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)