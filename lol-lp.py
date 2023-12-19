#!/usr/bin/env python
import src.plot as plot
import sys

# Summoner name should be first argument
summoner_name = sys.argv[1]

plot.plot(summoner_name)
