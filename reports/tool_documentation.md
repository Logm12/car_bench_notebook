# CAR-bench Agent Tool Documentation

This document provides a detailed description of each tool available to the CAR-bench voice assistant agent, including name, description, and parameter specifications.

## 1. Quan trọng nhất (Bắt buộc tuân thủ, Xác nhận & An toàn)

> [!IMPORTANT]
> **LÝ DO:** Các tool này bắt buộc phải đi kèm với xác nhận người dùng (`REQUIRES_CONFIRMATION`), thực hiện khử mơ hồ mức độ ưu tiên cao (`get_user_preferences`), kiểm tra an toàn thời tiết bắt buộc (`get_weather`) hoặc quản lý kế hoạch. Vi phạm quy trình của nhóm này sẽ bị trừ toàn bộ điểm (Reward = 0.0) ngay lập tức.

### `get_user_preferences`

**Description:** Retrieves user preferences for one or more specified categories and subcategories

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `preference_categories` | `object` | Yes | Categories of preferences to check for | - |

---

### `get_weather`

**Description:** Weather Information: gets the weather information for the specified location and the specified time (3h slot) plus the next time slot. Weather information includes temperature, wind speed, humidity, and condition (sunny, cloudy, rainy, foggy, etc.)

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `location_or_poi_id` | `string` | Yes | The location 'id' or point of interest (POI) 'id' to get the weather information | - |
| `month` | `number` | Yes | The month to get the weather information. | Min: 1; Max: 12 |
| `day` | `number` | Yes | The day to get the weather information. | Min: 1; Max: 31 |
| `time_hour_24hformat` | `number` | Yes | The time hour to get the weather information. | Min: 0; Max: 23 |
| `time_minutes` | `number` | No | The time minutes to get the weather information. | Min: 0; Max: 59 |

---

### `open_close_trunk_door`

**Description:** REQUIRES_CONFIRMATION, Vehicle Control: Open or close the trunk door of the car

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `action` | `string` | Yes | Whether to open or close the trunk door. | Enum: 'OPEN', 'CLOSE' |

---

### `planning_tool`

**Description:** A planning tool that allows creating and managing plans for solving complex tasks. Provides functionality for creating plans, updating plan steps, and tracking progress. Last step of the plan should always be to check if all user intents could be resolved and if not, to note and communicate which intents could not be resolved (because no available tool, data, etc.).

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `command` | `string` | Yes | The command to execute. Available commands: create, update, list, get, set_active, mark_steps, delete. | Enum: 'create', 'update', 'list', 'get', 'set_active', 'mark_steps', 'delete' |
| `plan_id` | `string` | No | Unique identifier for the plan. Required for create, update, set_active, and delete commands. Optional for get and mark_steps (uses active plan if not specified). | - |
| `title` | `string` | No | Title for the plan. Required for create command, optional for update command. | - |
| `steps` | `array` | No | List of plan steps. Each step must have a description and list of dependencies. Required for create command, optional for update command. | - |
| `step_updates` | `array` | No | List of step updates for mark_steps command. Each update can specify a step's status and notes. Only mark as completed if expected result is found, if another tool execution is needed for step mark as in_progress. | - |

---

### `send_email`

**Description:** REQUIRES_CONFIRMATION, Email Tool: sends an email with the specified message to the specified email adresses.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `content_message` | `string` | Yes | The content of the email message which is sent. Generate a suitable email message based on the user request if the user does not explicitely provide one. If there is no request about the content ask the user for it. | - |
| `email_addresses` | `array` | Yes | List of email adresses to send the email to. | - |

---

### `set_head_lights_high_beams`

**Description:** REQUIRES_CONFIRMATION, Vehicle Control: Turns the high beam headlights outside the car on or off.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the high beam headlights, False to turn off the high beam headlights. | - |

---

## 2. Quan trọng hơn (Quy định tương hỗ xe & Dẫn đường nâng cao)

> [!TIP]
> **LÝ DO:** Các tool điều khiển có độ phức tạp cao, đòi hỏi phải gọi tuần tự (như mở sunshade trước khi mở sunroof) hoặc tự động thay đổi các trạng thái liên đới (defrost/AC chỉnh fan speed/airflow direction). Nhóm này cũng gồm các điều khiển navigation động.

### `call_phone_by_number`

**Description:** Phone Tool: calls the specified phone number.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `phone_number` | `string` | Yes | The phone number to call. | - |

---

### `delete_current_navigation`

**Description:** Navigation Control: deletes the currently set navigation. Turns the navigation system to inactive and deletes all waypoints and routes.

**Parameters:** None

---

### `get_current_navigation_state`

**Description:** Navigation State Information: gets the navigation state including if the navigation is active and the currently selected route. The route information includes the current waypoint 'id's and the current selected route part 'id's. If parameter 'detailed_information' is set, additional information about the waypoint names, positions, and the route starts, destinations, distances, and durations is returned.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `detailed_information` | `boolean` | No | If False, only waypoint and route 'id's are returned. If True, additional information about the waypoint names, positions; and the route starts, destinations, distances, durations is returned. | - |

---

### `get_routes_from_start_to_destination`

**Description:** Routes information: gets the fastest route (plus alternative routes if existent) for the car between start and destination. Each route information includes name_via, distance in km, duration in hours and minutes, arrival time, road types (highway, urban, country roads, includes toll roads), and an route alias (first, second, third; additionaly fastest, shortest). Routes can be requested between locations or between a location and a point of interest.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `start_id` | `string` | Yes | The starting point of the route. The starting point has to be the location 'id' or a points of interest 'id'. | - |
| `destination_id` | `string` | Yes | The destination point of the route. The destination point has to be the location 'id' or a points of interest 'id'. | - |

---

### `navigation_add_one_waypoint`

**Description:** Navigation Control: adds the specified waypoint with the specified routes in the specified waypoint order. Only works if navigation system is active. Returns the navigation waypoint and routes with the waypoint and routes added.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `waypoint_id_to_add` | `string` | Yes | The 'id' of the waypoint to add to the route. | - |
| `waypoint_id_before_new_waypoint` | `string` | Yes | The 'id' of the waypoint before the new waypoint. | - |
| `waypoint_id_after_new_waypoint` | `string` | No | The 'id' of the waypoint after the new waypoint. Mandatory if the new waypoint is not the final destination. | - |
| `route_id_leading_to_new_waypoint` | `string` | Yes | The 'id' of the route leading to the new waypoint. Start has to match the 'waypoint_id_before_new_waypoint'. | - |
| `route_id_leading_away_from_new_waypoint` | `string` | No | The 'id' of the route leading away from the new waypoint. Destination has to match the 'waypoint_id_after_new_waypoint'. Mandatory if the new waypoint is not the final destination. | - |

---

### `navigation_replace_final_destination`

**Description:** Navigation Control: replaces the final destination and the specified route leading to the new destination. Only works if navigation system is active. Returns the navigation waypoint and routes with the new destination set.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `new_destination_id` | `string` | Yes | The 'id' of the new destination location or point of interest. | - |
| `route_id_leading_to_new_destination` | `string` | Yes | Route ID from route that leads to the new destination. Start has to match the destination of the previous route (if there is any). | - |

---

### `navigation_replace_one_waypoint`

**Description:** Navigation Control: replaces one waypoint and the specified routes leading to the new waypoint and away from the new waypoint. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the new waypoints set.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `waypoint_id_to_replace` | `string` | Yes | The 'id' of the waypoint to replace. | - |
| `new_waypoint_id` | `string` | Yes | The 'id' of the waypoint to include in the new route. | - |
| `route_id_leading_to_new_waypoint` | `string` | Yes | Route ID from route that leads to the new waypoint, destination of the route is the new waypoint. Start has to match the destination of the previous route (if there is any). | - |
| `route_id_leading_away_from_new_waypoint` | `string` | Yes | Route ID from the route that leads away from the new waypoint, start of the route is the new waypoint. Destination has to match the start of the next route (if there is any). | - |

---

### `open_close_sunroof`

**Description:** Vehicle Control: Open or close the sunroof in the car to a specified percentage: 0 (closed) to 100 (open)

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `percentage` | `number` | Yes | The percentage to open the sunroof, ranging from 0 to 100 | Min: 0; Max: 100 |

---

### `open_close_sunshade`

**Description:** Vehicle Control: Open or close the sunshade in the car to a specified percentage: 0 (closed) to 100 (open)

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `percentage` | `number` | Yes | The percentage to open the sunshade, ranging from 0 to 100 | Min: 0; Max: 100 |

---

### `open_close_window`

**Description:** Vehicle Control: Moves the specified window in the car to a certain percentage open or closed.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `window` | `string` | Yes | Which window to move. Use 'ALL' to refer to all windows. | Enum: 'ALL', 'DRIVER', 'PASSENGER', 'DRIVER_REAR', 'PASSENGER_REAR', 'RIGHT_REAR', 'LEFT_REAR' |
| `percentage` | `number` | Yes | Percentage to open or close the specified window or windows, ranging from 0 to 100. | Min: 0; Max: 100 |

---

### `set_air_conditioning`

**Description:** Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the air conditioning, False to turn off the air conditioning. | - |

---

### `set_fog_lights`

**Description:** Vehicle Control: Turns the fog lights outside the car on or off.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the fog lights, False to turn off the fog lights. | - |

---

### `set_head_lights_low_beams`

**Description:** Vehicle Control: Turns the low beam headlights outside the car on or off.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the low beam headlights, False to turn off the low beam headlights. | - |

---

### `set_new_navigation`

**Description:** Navigation Control: sets and starts new navigation in the navigation system. It fully replaces any previously set navigation. If multiple route 'id' are given it automatically sets a waypoint. It activates the navigation system and returns the waypoints set.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `route_ids` | `array` | Yes | Ordered list of route IDs to set for navigation. Order of list is from start, over optional waypoints, to destination. If multiple route 'id' are given, the destination of the first route has to match the start of next route. | - |

---

### `set_window_defrost`

**Description:** Vehicle Climate Control: Turns on or off the defrost of the specified window inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the defrost, False to turn off the defrost. | - |
| `defrost_window` | `string` | Yes | The window to turn on or off the defrost. | Enum: 'ALL', 'FRONT', 'REAR' |

---

## 3. Quan trọng (Truy vấn thông tin xe/môi trường & Tiện ích hỗ trợ)

> [!NOTE]
> **LÝ DO:** Các tool truy vấn thông tin cơ bản, tính toán số học, hoặc thay đổi các thông số thoải mái (ambient lights, seat heating level) ít bị ràng buộc bởi các điều kiện chính sách khắt khe của hệ thống.

### `calculate_charging_soc_by_time`

**Description:** Charging Information: Calculates the reached state of charge when charging the car for the specified time. Calculation is based on charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `charging_station_id` | `string` | Yes | The ID of the charging station. | - |
| `charging_station_plug_id` | `string` | Yes | The ID of the specific plug of the charging station where the car is connected to. | - |
| `start_state_of_charge` | `integer` | Yes | The start state of charge of the electric vehicle (in percentage). | Min: 0; Max: 100 |
| `charging_time` | `integer` | Yes | The charging time in minutes. | Min: 0 |

---

### `calculate_charging_time_by_soc`

**Description:** Charging Information: Calculates the charging time for charging from an start state of charge to a target state of charge of the car based charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `charging_station_id` | `string` | Yes | The ID of the charging station. | - |
| `charging_station_plug_id` | `string` | Yes | The ID of the specific plug of the charging station where the car is connected to. | - |
| `start_state_of_charge` | `integer` | Yes | The start state of charge of the electric vehicle (in percentage). | Min: 0; Max: 100 |
| `target_state_of_charge` | `integer` | No | The target state of charge of the electric vehicle (in percentage). If not specified, time until 80 percent and 100 percent is given. | Min: 0; Max: 100 |

---

### `calculate_datetime`

**Description:** Takes a datetime and adds specified times. It returns the new datetime

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `original_datetime` | `object` | Yes |  | - |
| `times_to_add` | `array` | Yes | Array of objects containing hours and minutes to add. Each object will be added to the original datetime | - |

---

### `calculate_math`

**Description:** Calculate the result of a mathematical expression.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `expression` | `string` | Yes | The mathematical expression to calculate, such as '2 + 2'. The expression can contain numbers, operators (+, -, *, /), parentheses, and spaces. | - |

---

### `convert_route_distance_and_time`

**Description:** Helper Tool: converts distance (in kilometer) into time (minutes) needed along specific route and vice versa.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `route_id` | `string` | Yes | The route_id for which conversion should happen. | - |
| `time_minutes` | `integer` | No | The time in minutes to convert into distance. | - |
| `distance_km` | `integer` | No | The distance in kilometer to convert into time. | - |

---

### `get_ambient_light_status_and_color`

**Description:** Vehicle Information: Get the status and color of the car ambient light (the soft, decorative lighting inside the cabin). Also referred to as 'surrounding light'.

**Parameters:** None

---

### `get_car_color`

**Description:** Vehicle Information: Get the outside color of the car.

**Parameters:** None

---

### `get_charging_specs_and_status`

**Description:** Charging Information: Get the charging specs of the car and current charging status of the electric vehicle. This includes battery_capacity_kwh, max_charging_power_ac, max_charging_power_dc, state_of_charge and remaining_range (calculated based on current power consumption, expected power consumption if route selected, or base power consumption if standing).

**Parameters:** None

---

### `get_climate_settings`

**Description:** Vehicle Information: Get the climate settings inside the car including current fan speed, fan airflow direction, air conditioning status, air circulation mode, and window defrost status.

**Parameters:** None

---

### `get_contact_id_by_contact_name`

**Description:** Contact Information: gets the contact 'id' for the specified contact name. You can search by first name, last name, or both.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `contact_first_name` | `string` | No | The first name of the contact to get the 'id' for. | - |
| `contact_last_name` | `string` | No | The last name of the contact to get the 'id' for. | - |

---

### `get_contact_information`

**Description:** Contact Information: gets the contact information for the specified contact 'id's. Contact information includes name, phone number, and email.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `contact_ids` | `array` | Yes | List of contact 'id's to get the contact information for. | - |

---

### `get_distance_by_soc`

**Description:** Charging Information: Get the distance able to drive for a specified initial state until a final state of charge of the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `initial_state_of_charge` | `integer` | Yes | The initial state of charge of the electric vehicle. | Min: 0; Max: 100 |
| `final_state_of_charge` | `integer` | No | The final state of charge of the electric vehicle. Defaults to 0 (battery empty). | Min: 0; Max: 100 |

---

### `get_entries_from_calendar`

**Description:** Calendar Information: gets the entries (including meetings, events, appointment etc.) set in the calendar from the current day. Returns the entry start, duration, topic, and attendees.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `month` | `integer` | Yes | The month for which the calendar entries are requested. | - |
| `day` | `integer` | Yes | The day for which the calendar entries are requested. | - |

---

### `get_exterior_lights_status`

**Description:** Vehicle Information: Get the status of car exterior lights including headlights (low beam and high beam), and fog lights.

**Parameters:** None

---

### `get_fuel_information`

**Description:** Vehicle Information: Get information about the fuel type, fuel consumption, and remaining fuel.

**Parameters:** None

---

### `get_location_id_by_location_name`

**Description:** Location Information: gets the location 'id' for the specified location name or city name. It does not get the 'id' for points of interest.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `location` | `string` | Yes | The location name to get the 'id' for. | - |

---

### `get_reading_lights_status`

**Description:** Vehicle Information: Get the status of car reading lights (interior).

**Parameters:** None

---

### `get_seat_heating_level`

**Description:** Vehicle Information: Get the level of seat heating in the different seat zones.

**Parameters:** None

---

### `get_seats_occupancy`

**Description:** Vehicle Information: Get the occupancy of seats inside the car.

**Parameters:** None

---

### `get_steering_wheel_heating_level`

**Description:** Vehicle Information: Get the level of the steering wheel heating.

**Parameters:** None

---

### `get_sunroof_and_sunshade_position`

**Description:** Vehicle Information: Get information about the position of the car sunroof and sunshade.

**Parameters:** None

---

### `get_temperature_inside_car`

**Description:** Vehicle Information: Get the temperature in the different seat zones inside the car.

**Parameters:** None

---

### `get_trunk_door_position`

**Description:** Vehicle Information: Get information about the position of the car trunk door.

**Parameters:** None

---

### `get_vehicle_window_positions`

**Description:** Vehicle Information: Get the current position of the windows in the car.

**Parameters:** None

---

### `navigation_delete_destination`

**Description:** Navigation Control: deletes the destination from the route set, with this the last intermediate stop becomes the new destination. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the destination and corresponding route deleted.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `destination_id_to_delete` | `string` | Yes | The 'id' of the destination to delete. | - |

---

### `navigation_delete_waypoint`

**Description:** Navigation Control: deletes the specified waypoint from the route set. Additionaly the route replacing the routes via the waypoint has the provided and will be set. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the waypoint deleted and the replacing route set.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `waypoint_id_to_delete` | `string` | Yes | The 'id' of the waypoint to delete. | - |
| `route_id_without_waypoint` | `string` | Yes | The 'id' of the route that should be set without the waypoint instead of the routes via the waypoint. Start has the match the previous waypoint of the deleted waypoint and destination has to match the next waypoint of the deleted waypoint. | - |

---

### `search_poi_along_the_route`

**Description:** Points of Interest Search: searches for points of interest in the specified category along the specified route. Points of interest information includes name, position (long, lat), detour from route in km, detour from route in hour and minutes, opening hours, and phone number. Returns 3 points of interest with the smallest detour time (sorting can be changed to smallest detour distance with filter).

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `route_id` | `string` | Yes | The route_id to search for points of interest along the route. | - |
| `category_poi` | `string` | Yes | The category of the point of interest to search for. | Enum: 'airports', 'bakery', 'fast_food', 'parking', 'public_toilets', 'restaurants', 'supermarkets', 'charging_stations' |
| `at_kilometer` | `integer` | No | at what kilometer of the route to look for the place (with radius of 10 km). If not set, search is done along whole route. This parameter is required if category_poi is charging_stations. | - |
| `filters` | `array` | No | List of filter strings to apply to search results. any:: filters can be applied to all categories, charging_stations:: filters can be applied only if category is charging stations. Default sorting is by detour time. | - |

---

### `search_poi_at_location`

**Description:** Points of Interest Search: searches for points of interest in the specified category around the specified location. Points of interest information includes name, position (long, lat), distance from location in km, duration from location in hour and minutes, opening hours, and phone number.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `location_id` | `string` | Yes | The location 'id' to search for a POI | - |
| `category_poi` | `string` | Yes | The category of the point of interest to search for. | Enum: 'airports', 'bakery', 'fast_food', 'parking', 'public_toilets', 'restaurants', 'supermarkets', 'charging_stations' |
| `filters` | `array` | No | List of filter strings to apply to search results. any:: filters can be applied to all categories, charging_stations:: filters can be applied only if category is charging stations. | - |

---

### `set_air_circulation`

**Description:** Vehicle Climate Control: Set the mode of air circulation to draw fresh air or recirculate air inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `mode` | `string` | Yes | In which mode the air should be circulated. | Enum: 'FRESH_AIR', 'RECIRCULATION', 'AUTO' |

---

### `set_ambient_lights`

**Description:** Vehicle Control: Turns the ambient light inside the car on (including the color) or off. Ambient light is the soft, decorative lighting inside the cabin, also referred to as 'surrounding light.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `on` | `boolean` | Yes | True to turn on the specified ambient light, False to turn off the ambient light. | - |
| `lightcolor` | `string` | Yes | The color of the ambient light, None if the ambient light is turned off. | Enum: 'RED', 'GREEN', 'BLUE', 'YELLOW', 'WHITE', 'PINK', 'ORANGE', 'PURPLE', 'CYAN', 'NONE' |

---

### `set_climate_temperature`

**Description:** Vehicle Climate Control: Sets the climate inside the car to the specified temperature in the specified seat zones.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `temperature` | `number` | Yes | Sets the temperature of the AC inside the car in degree Celsius. Must be explicitly stated by the driver. | Min: 16; Max: 28 |
| `seat_zone` | `string` | Yes | The seat zone to set the temperature. | Enum: 'ALL_ZONES', 'DRIVER', 'PASSENGER' |

---

### `set_fan_airflow_direction`

**Description:** Vehicle Climate Control: Set fan airflow direction inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `direction` | `string` | Yes | The airflow direction to set the fans to. | Enum: 'FEET', 'HEAD', 'HEAD_FEET', 'WINDSHIELD', 'WINDSHIELD_FEET', 'WINDSHIELD_HEAD', 'WINDSHIELD_HEAD_FEET' |

---

### `set_fan_speed`

**Description:** Vehicle Climate Control: Sets the fan speed to the specified level inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `level` | `number` | Yes | The level to set the fan speed to. | Min: 0; Max: 5 |

---

### `set_reading_light`

**Description:** Vehicle Control: Turns the specified reading light in the car on or off.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `position` | `string` | Yes | Which reading light to turn on or off. Use 'ALL' to refer to all reading lights. | Enum: 'ALL', 'DRIVER', 'PASSENGER', 'DRIVER_REAR', 'PASSENGER_REAR', 'RIGHT_REAR', 'LEFT_REAR' |
| `on` | `boolean` | Yes | True to turn on the reading light, False to turn off the reading light. | - |

---

### `set_seat_heating`

**Description:** Vehicle Climate Control: Sets the seat heating inside the car to the specified seat zones.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `level` | `number` | Yes | The level to set the seat heating to. | Min: 0; Max: 3 |
| `seat_zone` | `string` | Yes | The seat zone to set the seat heating to. | Enum: 'ALL_ZONES', 'DRIVER', 'PASSENGER' |

---

### `set_steering_wheel_heating`

**Description:** Vehicle Climate Control: Sets the steering wheel heating to the specified level inside the car.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `level` | `number` | Yes | The level to set the steering wheel heating to. | Min: 0; Max: 3 |

---

### `think`

**Description:** Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning is needed.

**Parameters:**

| Name | Type | Required | Description | Details |
| --- | --- | --- | --- | --- |
| `thought` | `string` | Yes | A thought to think about. | - |

---
