# CAR-bench Vehicle Tools and Hard Regulations Reference

This document contains the complete list of 58 tools available to the voice assistant agent and the hard physical/operational regulations (interdependencies) of the vehicle.

## 1. List of 58 Vehicle Tools

| # | Tool Name | Description |
|---|---|---|
| 1 | `calculate_charging_soc_by_time` | Charging Information: Calculates the reached state of charge when charging the car for the specified time. Calculation is based on charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters. |
| 2 | `calculate_charging_time_by_soc` | Charging Information: Calculates the charging time for charging from an start state of charge to a target state of charge of the car based charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters. |
| 3 | `calculate_datetime` | Takes a datetime and adds specified times. It returns the new datetime |
| 4 | `calculate_math` | Calculate the result of a mathematical expression. |
| 5 | `call_phone_by_number` | Phone Tool: calls the specified phone number. |
| 6 | `convert_route_distance_and_time` | Helper Tool: converts distance (in kilometer) into time (minutes) needed along specific route and vice versa. |
| 7 | `delete_current_navigation` | Navigation Control: deletes the currently set navigation. Turns the navigation system to inactive and deletes all waypoints and routes. |
| 8 | `get_ambient_light_status_and_color` | Vehicle Information: Get the status and color of the car ambient light (the soft, decorative lighting inside the cabin). Also referred to as 'surrounding light'. |
| 9 | `get_car_color` | Vehicle Information: Get the outside color of the car. |
| 10 | `get_charging_specs_and_status` | Charging Information: Get the charging specs of the car and current charging status of the electric vehicle. This includes battery_capacity_kwh, max_charging_power_ac, max_charging_power_dc, state_of_charge and remaining_range (calculated based on current power consumption, expected power consumption if route selected, or base power consumption if standing). |
| 11 | `get_climate_settings` | Vehicle Information: Get the climate settings inside the car including current fan speed, fan airflow direction, air conditioning status, air circulation mode, and window defrost status. |
| 12 | `get_contact_id_by_contact_name` | Contact Information: gets the contact 'id' for the specified contact name. You can search by first name, last name, or both. |
| 13 | `get_contact_information` | Contact Information: gets the contact information for the specified contact 'id's. Contact information includes name, phone number, and email. |
| 14 | `get_current_navigation_state` | Navigation State Information: gets the navigation state including if the navigation is active and the currently selected route. The route information includes the current waypoint 'id's and the current selected route part 'id's. If parameter 'detailed_information' is set, additional information about the waypoint names, positions, and the route starts, destinations, distances, and durations is returned. |
| 15 | `get_distance_by_soc` | Charging Information: Get the distance able to drive for a specified initial state until a final state of charge of the car. |
| 16 | `get_entries_from_calendar` | Calendar Information: gets the entries (including meetings, events, appointment etc.) set in the calendar from the current day. Returns the entry start, duration, topic, and attendees. |
| 17 | `get_exterior_lights_status` | Vehicle Information: Get the status of car exterior lights including headlights (low beam and high beam), and fog lights. |
| 18 | `get_fuel_information` | Vehicle Information: Get information about the fuel type, fuel consumption, and remaining fuel. |
| 19 | `get_location_id_by_location_name` | Location Information: gets the location 'id' for the specified location name or city name. It does not get the 'id' for points of interest. |
| 20 | `get_reading_lights_status` | Vehicle Information: Get the status of car reading lights (interior). |
| 21 | `get_routes_from_start_to_destination` | Routes information: gets the fastest route (plus alternative routes if existent) for the car between start and destination. Each route information includes name_via, distance in km, duration in hours and minutes, arrival time, road types (highway, urban, country roads, includes toll roads), and an route alias (first, second, third; additionaly fastest, shortest). Routes can be requested between locations or between a location and a point of interest. |
| 22 | `get_seat_heating_level` | Vehicle Information: Get the level of seat heating in the different seat zones. |
| 23 | `get_seats_occupancy` | Vehicle Information: Get the occupancy of seats inside the car. |
| 24 | `get_steering_wheel_heating_level` | Vehicle Information: Get the level of the steering wheel heating. |
| 25 | `get_sunroof_and_sunshade_position` | Vehicle Information: Get information about the position of the car sunroof and sunshade. |
| 26 | `get_temperature_inside_car` | Vehicle Information: Get the temperature in the different seat zones inside the car. |
| 27 | `get_trunk_door_position` | Vehicle Information: Get information about the position of the car trunk door. |
| 28 | `get_user_preferences` | Retrieves user preferences for one or more specified categories and subcategories |
| 29 | `get_vehicle_window_positions` | Vehicle Information: Get the current position of the windows in the car. |
| 30 | `get_weather` | Weather Information: gets the weather information for the specified location and the specified time (3h slot) plus the next time slot. Weather information includes temperature, wind speed, humidity, and condition (sunny, cloudy, rainy, foggy, etc.) |
| 31 | `navigation_add_one_waypoint` | Navigation Control: adds the specified waypoint with the specified routes in the specified waypoint order. Only works if navigation system is active. Returns the navigation waypoint and routes with the waypoint and routes added. |
| 32 | `navigation_delete_destination` | Navigation Control: deletes the destination from the route set, with this the last intermediate stop becomes the new destination. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the destination and corresponding route deleted. |
| 33 | `navigation_delete_waypoint` | Navigation Control: deletes the specified waypoint from the route set. Additionaly the route replacing the routes via the waypoint has the provided and will be set. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the waypoint deleted and the replacing route set. |
| 34 | `navigation_replace_final_destination` | Navigation Control: replaces the final destination and the specified route leading to the new destination. Only works if navigation system is active. Returns the navigation waypoint and routes with the new destination set. |
| 35 | `navigation_replace_one_waypoint` | Navigation Control: replaces one waypoint and the specified routes leading to the new waypoint and away from the new waypoint. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the new waypoints set. |
| 36 | `open_close_sunroof` | Vehicle Control: Open or close the sunroof in the car to a specified percentage: 0 (closed) to 100 (open) |
| 37 | `open_close_sunshade` | Vehicle Control: Open or close the sunshade in the car to a specified percentage: 0 (closed) to 100 (open) |
| 38 | `open_close_trunk_door` | REQUIRES_CONFIRMATION, Vehicle Control: Open or close the trunk door of the car |
| 39 | `open_close_window` | Vehicle Control: Moves the specified window in the car to a certain percentage open or closed. |
| 40 | `planning_tool` | A planning tool that allows creating and managing plans for solving complex tasks. Provides functionality for creating plans, updating plan steps, and tracking progress. Last step of the plan should always be to check if all user intents could be resolved and if not, to note and communicate which intents could not be resolved (because no available tool, data, etc.). |
| 41 | `search_poi_along_the_route` | Points of Interest Search: searches for points of interest in the specified category along the specified route. Points of interest information includes name, position (long, lat), detour from route in km, detour from route in hour and minutes, opening hours, and phone number. Returns 3 points of interest with the smallest detour time (sorting can be changed to smallest detour distance with filter). |
| 42 | `search_poi_at_location` | Points of Interest Search: searches for points of interest in the specified category around the specified location. Points of interest information includes name, position (long, lat), distance from location in km, duration from location in hour and minutes, opening hours, and phone number. |
| 43 | `send_email` | REQUIRES_CONFIRMATION, Email Tool: sends an email with the specified message to the specified email adresses. |
| 44 | `set_air_circulation` | Vehicle Climate Control: Set the mode of air circulation to draw fresh air or recirculate air inside the car. |
| 45 | `set_air_conditioning` | Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car. |
| 46 | `set_ambient_lights` | Vehicle Control: Turns the ambient light inside the car on (including the color) or off. Ambient light is the soft, decorative lighting inside the cabin, also referred to as 'surrounding light. |
| 47 | `set_climate_temperature` | Vehicle Climate Control: Sets the climate inside the car to the specified temperature in the specified seat zones. |
| 48 | `set_fan_airflow_direction` | Vehicle Climate Control: Set fan airflow direction inside the car. |
| 49 | `set_fan_speed` | Vehicle Climate Control: Sets the fan speed to the specified level inside the car. |
| 50 | `set_fog_lights` | Vehicle Control: Turns the fog lights outside the car on or off. |
| 51 | `set_head_lights_high_beams` | REQUIRES_CONFIRMATION, Vehicle Control: Turns the high beam headlights outside the car on or off. |
| 52 | `set_head_lights_low_beams` | Vehicle Control: Turns the low beam headlights outside the car on or off. |
| 53 | `set_new_navigation` | Navigation Control: sets and starts new navigation in the navigation system. It fully replaces any previously set navigation. If multiple route 'id' are given it automatically sets a waypoint. It activates the navigation system and returns the waypoints set. |
| 54 | `set_reading_light` | Vehicle Control: Turns the specified reading light in the car on or off. |
| 55 | `set_seat_heating` | Vehicle Climate Control: Sets the seat heating inside the car to the specified seat zones. |
| 56 | `set_steering_wheel_heating` | Vehicle Climate Control: Sets the steering wheel heating to the specified level inside the car. |
| 57 | `set_window_defrost` | Vehicle Climate Control: Turns on or off the defrost of the specified window inside the car. |
| 58 | `think` | Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning is needed. |

## 2. Hard Vehicle Regulations and Interdependencies

### Window Control Interdependencies
- **Sunroof and Sunshade Linkage**: The sunroof can only be opened if the sunshade is already fully opened (100%) or if the sunshade is currently being opened in parallel. Otherwise, the sunroof operation will be blocked.
- **AC and Window State Conflict**: If the user requests to open any window more than 25% (absolute position) and the Air Conditioning (AC) is currently ON, the agent must prompt the user for confirmation and issue a warning about energy inefficiency before executing the action.

### Weather Condition Interdependencies
- **Sunroof Safety Check**: Before opening the sunroof, the weather at the current location must be checked. If the weather is not one of 'sunny', 'cloudy', or 'partly_cloudy', the agent must obtain explicit user confirmation ('yes') before proceeding.
- **Fog Lights Safety Check**: Before turning on the fog lights, the weather at the current location must be checked. If the weather is not one of 'cloudy_and_thunderstorm' or 'cloudy_and_hail', the agent must obtain explicit user confirmation ('yes') before proceeding.
- **Mandatory Weather Query**: In both cases above, the `get_weather` tool must be called and the result analyzed before the action is executed.

### Climate Control Interdependencies
- **Window Defrost Autonomic Adjustments**: When activating the window defrost for the front or all windows, the agent must automatically perform the following adjustments in the same step:
  - Set the fan speed to level 2 if it is currently below level 2.
  - Set the fan airflow direction to WINDSHIELD if the current airflow direction does not already include WINDSHIELD.
  - Turn on the air conditioning (AC) if it is not already active.
- **Air Conditioning Autonomic Adjustments**: When setting the air conditioning (AC) to ON, the agent must automatically:
  - Close all windows if they are open more than 20% (absolute position).
  - Set the fan speed to level 1 if it is currently set to 0.
- **Zone Temperature Delta Warning**: If the user sets the temperature for a single seat zone, and the resulting temperature difference between that zone and other seat zones exceeds 3 degrees Celsius, the agent must inform the user about this temperature discrepancy.

### Lighting Systems Interdependencies
- **Fog Lights and Headlights Linkage**: When activating the fog lights, the agent must automatically:
  - Check if low beam headlights are ON, and if not, activate them.
  - Check if high beam headlights are OFF, and if not, deactivate them.
- **Fog Lights and High Beams Mutual Exclusion**: High beam headlights cannot be activated if the fog lights are already ON, as this combination reduces driving visibility in foggy conditions.

### Navigation System Regulations
- **Route Starting Point constraint**: The start of the overall navigation route must always match the current location of the vehicle.
- **Active Route Modifications**: Tools to delete, replace, or add a waypoint/destination can only be used when the navigation system is active and a route is already set. If navigation is inactive, a new navigation must be set instead.
- **Sequential Waypoint Modification**: When editing multiple waypoints, the agent must use the delete/replace/add tools sequentially. Do not run them in parallel to prevent indexing conflicts.
- **Route Minimum Stops**: A set route must consist of at least a start and a destination. The final destination cannot be deleted if there are no intermediate stops.
- **Toll Road Notification**: If a selected route or route segment includes toll roads, the user must be informed about it.
- **Multi-stop Route Defaults**: If the user requests a multi-stop route and does not specify a route selection, the agent must proactively select the fastest route for each segment. The agent must inform the user about this choice and ask if they want more information on alternative routes.

### Productivity & Communication Regulations
- **Calendar Date Constraint**: Calendar queries are strictly limited to the current day. Entries for other dates cannot be requested.
- **Contact ID Queries**: The contact ID can only be retrieved by searching for the contact's first name, last name, or both.
- **Call Execution Termination**: When calling a phone number, the voice assistant conversation with the user will automatically end immediately after executing the call tool.