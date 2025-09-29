import pathlib
import pytmc
from pytmc import parser
from pytmc.bin import template 

# plc = parser.parse("/opt/epics/iocs/lcsl-motion-samples/lcls-motion-test.tsproj").top_level_plc.projects["lclsPLCMotionTest"]

# motors = template.get_motors(plc)
# for mot in motors:
    # print(mot)

project = parser.parse("/opt/epics/iocs/motion-abstraction/lcls-motion-test.tsproj")
for plc in project.plcs:
   symbol_by_type = template.get_symbols_by_type(plc)
   stages = symbol_by_type.get("Symbol_FB_MotionStage", [])
   print(f"stages: {stages}.")
   # motors = template.get_motors(plc)
   #print(f"In PLC {plc.name}, found {len(motors)} pragma'd motor symbols.")
   #print(f"In PLC {plc.name}, found {len(motors)} pragma'd motor symbols,motor: {motors}.")
