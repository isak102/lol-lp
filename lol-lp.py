#!/usr/bin/env python
import argparse
import asyncio
import logging

import src.mobalytics_query as api
import src.plot as plot

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")


parser = argparse.ArgumentParser(description="League of Legends LP history")
parser.add_argument("-i", "--riot-id", required=True, help="Riot ID of the player")
parser.add_argument("-r", "--region", required=True, help="Region of the player")
args = parser.parse_args()

try:
    pages = asyncio.run(api.get_lphistory(args.riot_id, args.region.upper()))
except Exception as e:
    print(f"Error fetching pages: {e}")
    exit(1)

plot.plot(args.riot_id, pages)
