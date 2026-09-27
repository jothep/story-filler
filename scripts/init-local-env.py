#!/usr/bin/env python3
"""Create a private local Compose environment without displaying credentials."""

import argparse
import os
from pathlib import Path
import secrets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.env'))
    args = parser.parse_args()
    content = (
        '# Local development only. Do not commit this file.\n'
        f'DB_PASSWORD={secrets.token_hex(32)}\n'
        f'DJANGO_SECRET_KEY={secrets.token_hex(64)}\n'
    )
    try:
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.exit(1, f'{args.output} already exists; no values were changed.\n')
    with os.fdopen(fd, 'w') as output:
        output.write(content)
    print(f'Created {args.output} with private permissions; credentials were not displayed.')


if __name__ == '__main__':
    main()
