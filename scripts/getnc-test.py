import pathlib
import pytmc
from pytmc import parser
from pytmc.bin import template

def test_get_nc():
    # Arrange: Parse a sample project file containing NC block
    project_file = pathlib.Path("/opt/epics/iocs/lcsl-motion-samples/lcls-motion-test.tsproj")
    root = parser.parse(project_file)
    top_level_project = root.top_level_project  # usually the way to access TopLevelProject

    # Act
    nc = template.get_nc(top_level_project)

    # Assert
    assert nc is not None, "NC block should be found"
    assert isinstance(nc, parser.NC)
    assert hasattr(nc, "axes")  # or any attribute your NC object should have

    # (Optional) print info for demo/debug
    print("Found NC block:", nc)
    print("Axes:", getattr(nc, "axes", []))

test_get_nc()
