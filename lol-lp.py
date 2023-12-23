#!/usr/bin/env python
import argparse
import logging

import src.util as util

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")

parser = argparse.ArgumentParser(description="League of Legends LP history")

parser.add_argument(
    "-s", "--select", action="store_true", help="Select a player interactively"
)
parser.add_argument("-i", "--riot-id", help="Riot ID of the player")
parser.add_argument("-r", "--region", help="Region of the player")

args = parser.parse_args()

if args.select:
    import src.select_player as select_player

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
    import asyncio

    import src.api as api
    import src.data_processing as data_processing

    if args.select:
        util.notif(f"Fetching pages for {args.riot_id}...")
    pages = asyncio.run(api.get_lphistory(args.riot_id, args.region.upper()))

    if len(pages) == 0:
        if args.select:
            util.notif(f"No data found.", 5000)
        exit(0)

    if args.select:
        util.notif(f"Merging thresholds...")
    thresholds = data_processing.merge_thresholds(
        [page["thresholds"] for page in pages], args.region.upper()
    )

except Exception as e:
    error_msg = "Error getting data"
    print(f"{error_msg}: {e}")
    if args.select:
        util.notif(f"❌ {error_msg}", 5000)
    exit(1)

if args.select:
    util.notif("Done", 1)

import src.plot as plot

plot.plot(args.riot_id, args.region.upper(), pages, thresholds)
