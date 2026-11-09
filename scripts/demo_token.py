# Copyright (c) 2026 Sabareesh M (saba1207B). All Rights Reserved.
#
# This source code is proprietary and confidential.
#
# Unauthorized copying, redistribution, modification, or use — including
# any use for artificial intelligence / machine learning training —
# is strictly prohibited.
#
# See the LICENSE and COPYRIGHT files in the repository root for full terms.

"""Issue a local-only development token for the offline pilot."""

import argparse

from aquasentinel.config import get_settings
from aquasentinel.security import create_access_token


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", default="local-demo-user")
    parser.add_argument("--role", choices=["researcher", "authority"], default="researcher")
    args = parser.parse_args()
    if not get_settings().demo_mode:
        raise SystemExit("Demo token generation is disabled outside demo mode")
    print(create_access_token(args.subject, [args.role], ["tn-coimbatore"]))


if __name__ == "__main__":
    main()
