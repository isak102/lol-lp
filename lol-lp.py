#!/usr/bin/env python
import argparse
import asyncio
import logging

import src.mobalytics_query as api
import src.plot as plot
import src.select_player as select_player

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")

parser = argparse.ArgumentParser(description="League of Legends LP history")

parser.add_argument(
    "-s", "--select", action="store_true", help="Select a player interactively"
)
parser.add_argument("-i", "--riot-id", help="Riot ID of the player")
parser.add_argument("-r", "--region", help="Region of the player")

args = parser.parse_args()

if args.select:
    if args.riot_id or args.region:
        parser.error(
            "Do not provide -i/--riot-id or -r/--region when using -s/--select"
        )
    args.riot_id, args.region = select_player.select_player()
elif not args.riot_id or not args.region:
    parser.error(
        "Both -i/--riot-id and -r/--region are required when not using -s/--select"
    )

try:
    pages = asyncio.run(api.get_lphistory(args.riot_id, args.region.upper()))
except Exception as e:
    print(f"Error fetching pages: {e}")
    exit(1)

plot.plot(args.riot_id, pages)
