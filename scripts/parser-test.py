# Import your module - here, assume it's named mytwincat.py, otherwise adjust
import pathlib
import pytmc
from pytmc import parser, pragmas  # <-- Replace with your filename if different
from pytmc.bin import template 

# Path to a sample TwinCAT file (tsproj, xti, tmc, etc.)
filename = pathlib.Path("/opt/epics/iocs/motion-abstraction/lcls-motion-test.tsproj")  # Use your actual file path

# Call parse
twincat_root = parser.parse(filename)

# Print info about result
#print("Parsed root:", twincat_root)
#print("Type:", type(twincat_root))
#print("Name:", getattr(twincat_root, 'name', None))
#print("Children:", twincat_root._children)
#print("keys:", twincat_root.plcs_by_name.keys())
plcs = twincat_root.plcs_by_name['lclsPLCMotionTest']
#print(type(plcs))
#print(plcs)
#print(plcs.port)
#print(plcs.ams_id)
#print(plcs.target_ip)
print(plcs.links)
#print(plcs.get_source_code())
#print(template.get_library_versions(plcs))
#symbols = template.get_symbols_by_type(plcs)
#stages = symbols.get("Symbol_ST_MotionEpicsInterface", [])
#for stage in stages:
#    print(f"{type(stage)} : {pragmas.has_pragma(stage)}")
#    for pragma in pragmas.get_pragma(stage, name='pytmc'):
#    	print(f"{pragma}")
#print (template.get_motors(plcs))
#print(symbol.qualified_type_name)

