#!/usr/bin/env python3
"""
Fake `sensors -j` emulator: randomly generates a given number temp/hum.
ENV vars:
  NUM_TEMPS (int): number of temp-sensors (default 2)
  NUM_HUMS  (int): number of hum-sensors (default 2)
"""
import os, json, random

num_temps = int(os.getenv("NUM_TEMPS", 2))
num_hums  = int(os.getenv("NUM_HUMS", 2))

chip = {}
for i in range(1, num_temps + 1):
    chip[f"temp{i}_input"] = round(random.uniform(-30, 30) * 1000, 2)
for i in range(1, num_hums + 1):
    chip[f"humidity{i}_input"] = round(random.uniform(0, 100) * 1000, 2)

print(json.dumps({"emulator": chip}))
