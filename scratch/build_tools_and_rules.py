import re
from pathlib import Path

# Paths
workspace_dir = Path("e:/VinAI/VSG/car-bench-ijcai-vsf")
doc_file = workspace_dir / "reports" / "tool_documentation.md"
output_file = workspace_dir / "reports" / "vehicle_tools_and_rules.md"

# Read tool_documentation.md
with open(doc_file, "r", encoding="utf-8") as f:
    content = f.read()

# Extract tools: Name and Description
# Form of:
# ### `tool_name`
# **Description:** ...
tool_pattern = re.compile(r"### `([^`]+)`\n\n\*\*Description:\*\* ([^\n]+)")
tools = tool_pattern.findall(content)

md_content = []
md_content.append("# CAR-bench Vehicle Tools and Hard Regulations Reference\n")
md_content.append("This document contains the complete list of 58 tools available to the voice assistant agent and the hard physical/operational regulations (interdependencies) of the vehicle.\n")

md_content.append("## 1. List of 58 Vehicle Tools\n")
md_content.append("| # | Tool Name | Description |")
md_content.append("|---|---|---|")

for idx, (name, desc) in enumerate(sorted(tools, key=lambda x: x[0]), 1):
    md_content.append(f"| {idx} | `{name}` | {desc} |")

md_content.append("\n## 2. Hard Vehicle Regulations and Interdependencies\n")

rules = [
    "### Window Control Interdependencies",
    "- **Sunroof and Sunshade Linkage**: The sunroof can only be opened if the sunshade is already fully opened (100%) or if the sunshade is currently being opened in parallel. Otherwise, the sunroof operation will be blocked.",
    "- **AC and Window State Conflict**: If the user requests to open any window more than 25% (absolute position) and the Air Conditioning (AC) is currently ON, the agent must prompt the user for confirmation and issue a warning about energy inefficiency before executing the action.",
    "",
    "### Weather Condition Interdependencies",
    "- **Sunroof Safety Check**: Before opening the sunroof, the weather at the current location must be checked. If the weather is not one of 'sunny', 'cloudy', or 'partly_cloudy', the agent must obtain explicit user confirmation ('yes') before proceeding.",
    "- **Fog Lights Safety Check**: Before turning on the fog lights, the weather at the current location must be checked. If the weather is not one of 'cloudy_and_thunderstorm' or 'cloudy_and_hail', the agent must obtain explicit user confirmation ('yes') before proceeding.",
    "- **Mandatory Weather Query**: In both cases above, the `get_weather` tool must be called and the result analyzed before the action is executed.",
    "",
    "### Climate Control Interdependencies",
    "- **Window Defrost Autonomic Adjustments**: When activating the window defrost for the front or all windows, the agent must automatically perform the following adjustments in the same step:",
    "  - Set the fan speed to level 2 if it is currently below level 2.",
    "  - Set the fan airflow direction to WINDSHIELD if the current airflow direction does not already include WINDSHIELD.",
    "  - Turn on the air conditioning (AC) if it is not already active.",
    "- **Air Conditioning Autonomic Adjustments**: When setting the air conditioning (AC) to ON, the agent must automatically:",
    "  - Close all windows if they are open more than 20% (absolute position).",
    "  - Set the fan speed to level 1 if it is currently set to 0.",
    "- **Zone Temperature Delta Warning**: If the user sets the temperature for a single seat zone, and the resulting temperature difference between that zone and other seat zones exceeds 3 degrees Celsius, the agent must inform the user about this temperature discrepancy.",
    "",
    "### Lighting Systems Interdependencies",
    "- **Fog Lights and Headlights Linkage**: When activating the fog lights, the agent must automatically:",
    "  - Check if low beam headlights are ON, and if not, activate them.",
    "  - Check if high beam headlights are OFF, and if not, deactivate them.",
    "- **Fog Lights and High Beams Mutual Exclusion**: High beam headlights cannot be activated if the fog lights are already ON, as this combination reduces driving visibility in foggy conditions.",
    "",
    "### Navigation System Regulations",
    "- **Route Starting Point constraint**: The start of the overall navigation route must always match the current location of the vehicle.",
    "- **Active Route Modifications**: Tools to delete, replace, or add a waypoint/destination can only be used when the navigation system is active and a route is already set. If navigation is inactive, a new navigation must be set instead.",
    "- **Sequential Waypoint Modification**: When editing multiple waypoints, the agent must use the delete/replace/add tools sequentially. Do not run them in parallel to prevent indexing conflicts.",
    "- **Route Minimum Stops**: A set route must consist of at least a start and a destination. The final destination cannot be deleted if there are no intermediate stops.",
    "- **Toll Road Notification**: If a selected route or route segment includes toll roads, the user must be informed about it.",
    "- **Multi-stop Route Defaults**: If the user requests a multi-stop route and does not specify a route selection, the agent must proactively select the fastest route for each segment. The agent must inform the user about this choice and ask if they want more information on alternative routes.",
    "",
    "### Productivity & Communication Regulations",
    "- **Calendar Date Constraint**: Calendar queries are strictly limited to the current day. Entries for other dates cannot be requested.",
    "- **Contact ID Queries**: The contact ID can only be retrieved by searching for the contact's first name, last name, or both.",
    "- **Call Execution Termination**: When calling a phone number, the voice assistant conversation with the user will automatically end immediately after executing the call tool."
]

md_content.extend(rules)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(md_content))

print(f"File written successfully to {output_file} containing {len(tools)} tools.")
