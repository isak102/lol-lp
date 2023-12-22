#!/usr/bin/env python
import src.plot as plot
import src.mobalytics_query as api
import asyncio
import sys

# Summoner name should be first argument
summoner_name = sys.argv[1]  # TODO: get region here

pages = asyncio.run(api.get_lphistory(summoner_name, region="EUW"))
for page in pages:
    if page is None:
        print("Error fetching pages")
        sys.exit(1)
plot.plot(summoner_name, pages)  # type: ignore
