import pathlib
import pytmc
from pytmc import parser
from pytmc.bin import template

def test_nc_axis_and_nc_to_plc_link():
    # Arrange: Parse sample project and select a PLC
    project_file = "/opt/epics/iocs/motion-abstraction/lcls-motion-test.tsproj"
    project = parser.parse(project_file)
    top_level_plc = project.top_level_plc
    plc_dict = top_level_plc.projects
    #print(plc_dict)
    plc = next(iter(plc_dict.values()))
    #print(plc)
    # Get motion stage motors
    motors = template.get_motors(plc)
    print (motors)
    #assert motors, "No motors (ST_MotionStage symbols) found in PLC"
    #stage = motors[0]
    #print(stage)
    #print(f"\nTesting for stage symbol: {stage.name}")

    # Test nc_to_plc_link
    #link = stage.nc_to_plc_link()
    #print(f"nc_to_plc_link result: {link}")
    #print(f"Link.a: {link.a}")
    #print(f"Link.b: {link.b}")
    #print(f"Link parent name: {link.parent.name}")

    #assert link is not None, "nc_to_plc_link should not be None"
    #assert isinstance(link, parser.Link), "nc_to_plc_link should return a Link"

    # Test nc_axis
    # axis = stage.nc_axis()
    # print(f"nc_axis result: {axis}")

    # assert axis is not None, "nc_axis should not be None"
    # assert hasattr(axis, "name"), "NC Axis should have a name attribute"
    # print(f"NC Axis name: {axis.name}")

    # # Additional clarity: show all axes in NC if found
    # nc_obj = None
    # # Try to get the NC object using get_nc if implemented
    # if hasattr(parser, "get_nc"):
        # nc_obj = template.get_nc(project.top_level_project)
    # if not nc_obj:
        # # Try via root
        # nc_candidates = list(project.root.find(parser.NC, recurse=True))
        # if nc_candidates:
            # nc_obj = nc_candidates[0]
    # if nc_obj:
        # print("All axes in NC object:")
        # for axis_name, axis_obj in getattr(nc_obj, "axis_by_name", {}).items():
            # print(f"  {axis_name}: {axis_obj}")

    # print(f"\nTested nc_axis and nc_to_plc_link for motion stage {stage.name}.")

test_nc_axis_and_nc_to_plc_link()
