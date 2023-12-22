#!/usr/bin/env python
import src.plot as plot
import src.mobalytics_query as api
import asyncio
import argparse

parser = argparse.ArgumentParser(description="League of Legends LP history")
parser.add_argument("-i", "--riot-id", required=True, help="Riot ID of the player")
parser.add_argument("-r", "--region", required=True, help="Region of the player")
args = parser.parse_args()

pages = asyncio.run(api.get_lphistory(args.riot_id, args.region.upper()))
for page in pages:
    if page is None:
        print("Error fetching pages")
        exit(1)

plot.plot(args.riot_id, pages)  # type: ignore
