import sys
import pytmc
from pytmc import parser
from pytmc.parser import Symbol

def extract_stage_axis_links(tree: pytmc.parser.Symbol):
    """
    Walk TwincatItem tree (root from Parser.parse) and extract
    all ST_MotionStage variables with an axis-link pragma.

    Supports both array and scalar variables.
    """
    results = []

    # Walk all items (recursively)
    for item in tree.walk():
        if not isinstance(item, TmcSymbol):
            continue

        # Find axis-link pragma
        axis_link = None
        for key, value in item.pragmas_dict.items():
            if key.startswith("axis-link"):
                axis_link = value
                break

        if axis_link is None:
            continue

        # Handle arrays vs scalars
        if item.array_info:
            arr = item.array_info[0]
            lbound, num = arr["lbound"], arr["elements"]
            if "[" not in axis_link:
                # Standard mapping using array index
                for i in range(lbound, lbound + num):
                    stage = f"{item.full_name}[{i}]"
                    axis = f"{axis_link}[{i}]"
                    results.append((stage, axis))
            elif "$INDEX$" in axis_link:
                for i in range(lbound, lbound + num):
                    stage = f"{item.full_name}[{i}]"
                    axis = axis_link.replace("$INDEX$", str(i))
                    results.append((stage, axis))
            else:
                print(f"Warning: Array var '{item.full_name}' has axis-link '{axis_link}' not handled as array mapping")
        else:
            # Scalar variable
            results.append((item.full_name, axis_link))
    return results

### --- USAGE EXAMPLE ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <project.tmc>")
        sys.exit(1)
    tmc_path = sys.argv[1]
    print(f"Parsing: {tmc_path} ...")
    with open(tmc_path, "r", encoding="utf-8") as f:
        xml = f.read()
    root = parser.parse(xml)
    links = extract_stage_axis_links(root)
    print("Stage Variable        -->   Axis Reference")
    print("-------------------        --------------")
    for stage, axis in links:
        print(f"{stage:22} --> {axis}")
