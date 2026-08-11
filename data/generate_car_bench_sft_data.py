#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""CAR-Bench SFT dataset generator for OpenAI Chat Completions format."""

import json
import os
import random
import re
from uuid import uuid4

random.seed(42)

TOOL_ALIAS_MAP = {
    "set_ambient_lights": "set_ambient_lighting",
    "open_close_window": "open_close_windows",
    "set_climate_temperature": "set_temperature",
    "set_head_lights_low_beams": "set_head_lights",
    "call_phone_by_number": "make_phone_call",
    "set_new_navigation": "start_navigation",
    "get_routes_from_start_to_destination": "get_routes",
    "get_route_information": "get_routes",
    "get_routes_between_locations": "get_routes",
    "search_along_route_w_coordinates": "search_poi_along_the_route",
    "search_points_of_interest": "search_poi_at_location",
    "get_ev_charging_status": "get_charging_status",
    "get_charging_specs_and_status": "get_charging_status",
    "start_stop_ev_charging": "get_charging_status",
    "get_vehicle_window_positions": "get_window_positions",
    "get_vehicle_sunroof_and_sunshade_position": "get_sunroof_and_sunshade_position",
    "get_vehicle_climate_settings": "get_climate_settings",
    "get_vehicle_exterior_lights_status": "get_exterior_lights_status",
    "get_vehicle_seat_heating_level": "get_seat_heating_level",
    "get_vehicle_steering_wheel_heating_level": "get_steering_wheel_heating_level",
    "get_vehicle_reading_lights_status": "get_reading_lights_status",
    "get_vehicle_ambient_light_status_and_color": "get_ambient_light_status_and_color",
    "get_vehicle_temperature_inside_car": "get_temperature_inside_car",
    "get_vehicle_trunk_door_position": "get_trunk_door_position",
    "get_vehicle_seats_occupancy": "get_seats_occupancy",
    "get_vehicle_fuel_information": "get_fuel_information",
    "navigation_delete_destination": "navigation_delete_final_destination",
    "navigation_delete_waypoint": "navigation_delete_one_waypoint",
    "navigation_add_waypoint": "navigation_add_one_waypoint",
    "navigation_replace_waypoint": "navigation_replace_one_waypoint",
    "get_vehicle_status": "get_climate_settings",
}

def normalize_tool_name(name):
    if not name:
        return "get_climate_settings"
    if name in ALL_58_CAR_TOOLS:
        return name
    if name in TOOL_ALIAS_MAP:
        return TOOL_ALIAS_MAP[name]
    if name.startswith("get_vehicle_"):
        stripped = name.replace("get_vehicle_", "get_")
        if stripped in ALL_58_CAR_TOOLS:
            return stripped
    if re.match(r"^[a-zA-Z0-9_]+$", str(name)):
        ALL_58_CAR_TOOLS[name] = {
            "name": name,
            "description": f"Car voice assistant function {name}.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
        return name
    return name

ALL_58_CAR_TOOLS = {
    "open_close_sunroof": {
        "name": "open_close_sunroof",
        "description": "Open or close the sunroof to a specified percentage (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {
                "percentage": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Opening percentage (0 = closed, 100 = fully open)"}
            },
            "required": ["percentage"]
        }
    },
    "open_close_sunshade": {
        "name": "open_close_sunshade",
        "description": "Open or close the sunshade to a specified percentage (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["open", "close"]},
                "sunshade": {"type": "string", "enum": ["front", "rear", "all"]},
                "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
            },
            "required": ["action", "sunshade", "percentage"]
        }
    },
    "open_close_trunk_door": {
        "name": "open_close_trunk_door",
        "description": "Open or close the vehicle trunk door. REQUIRES USER CONFIRMATION.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["open", "close"]}
            },
            "required": ["action"]
        }
    },
    "open_close_windows": {
        "name": "open_close_windows",
        "description": "Open or close specific power windows (0 to 100%).",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["open", "close"]},
                "window": {"type": "string", "enum": ["front_left", "front_right", "rear_left", "rear_right", "all"]},
                "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
            },
            "required": ["action", "window"]
        }
    },
    "set_air_circulation": {
        "name": "set_air_circulation",
        "description": "Set air circulation mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["AUTO", "FRESH_AIR", "RECIRCULATION"]}
            },
            "required": ["mode"]
        }
    },
    "set_air_conditioning": {
        "name": "set_air_conditioning",
        "description": "Turn air conditioning ON or OFF.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"}
            },
            "required": ["on"]
        }
    },
    "set_ambient_lighting": {
        "name": "set_ambient_lighting",
        "description": "Set interior ambient lighting color and status.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"},
                "lightcolor": {"type": "string", "enum": ["BLUE", "RED", "PURPLE", "WHITE", "GREEN", "AMBER", "CYAN", "OFF"]}
            },
            "required": ["on", "lightcolor"]
        }
    },
    "set_temperature": {
        "name": "set_temperature",
        "description": "Set target climate temperature for seat zones (16°C to 28°C).",
        "parameters": {
            "type": "object",
            "properties": {
                "temperature": {"type": "number", "minimum": 16.0, "maximum": 28.0},
                "zone": {"type": "string", "enum": ["driver", "passenger", "rear_left", "rear_right", "all"]}
            },
            "required": ["temperature"]
        }
    },
    "set_fan_airflow_direction": {
        "name": "set_fan_airflow_direction",
        "description": "Set fan airflow direction.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["HEAD", "FEET", "HEAD_FEET", "WINDSHIELD", "WINDSHIELD_FEET"]}
            },
            "required": ["direction"]
        }
    },
    "set_fan_speed": {
        "name": "set_fan_speed",
        "description": "Set climate fan speed level (0 to 5).",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 5}
            },
            "required": ["level"]
        }
    },
    "set_fog_lights": {
        "name": "set_fog_lights",
        "description": "Turn front fog lights ON or OFF. Weather dependency apply.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"}
            },
            "required": ["on"]
        }
    },
    "set_head_lights_high_beams": {
        "name": "set_head_lights_high_beams",
        "description": "Turn high beam headlights ON or OFF. REQUIRES USER CONFIRMATION.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"}
            },
            "required": ["on"]
        }
    },
    "set_head_lights": {
        "name": "set_head_lights",
        "description": "Turn low beam headlights ON or OFF.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"}
            },
            "required": ["on"]
        }
    },
    "set_reading_light": {
        "name": "set_reading_light",
        "description": "Turn reading light ON or OFF for a specific seat zone.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"},
                "position": {"type": "string", "enum": ["DRIVER", "PASSENGER", "DRIVER_REAR", "PASSENGER_REAR"]}
            },
            "required": ["on", "position"]
        }
    },
    "set_seat_heating": {
        "name": "set_seat_heating",
        "description": "Set seat heating level (0 to 3) for a seat zone.",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 3},
                "seat": {"type": "string", "enum": ["driver", "passenger", "rear_left", "rear_right"]}
            },
            "required": ["level", "seat"]
        }
    },
    "set_steering_wheel_heating": {
        "name": "set_steering_wheel_heating",
        "description": "Set steering wheel heating level (0 to 3).",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 3}
            },
            "required": ["level"]
        }
    },
    "set_window_defrost": {
        "name": "set_window_defrost",
        "description": "Activate or deactivate windshield defrost system.",
        "parameters": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean"},
                "defrost_window": {"type": "string", "enum": ["FRONT", "REAR", "BOTH"]}
            },
            "required": ["on", "defrost_window"]
        }
    },
    "get_ambient_light_status_and_color": {
        "name": "get_ambient_light_status_and_color",
        "description": "Query ambient light color and status.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_car_color": {
        "name": "get_car_color",
        "description": "Query exterior car color.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_climate_settings": {
        "name": "get_climate_settings",
        "description": "Query climate control settings.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_exterior_lights_status": {
        "name": "get_exterior_lights_status",
        "description": "Query exterior lights status.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_fuel_information": {
        "name": "get_fuel_information",
        "description": "Query fuel level or battery state of charge.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_reading_lights_status": {
        "name": "get_reading_lights_status",
        "description": "Query reading lights status.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_seat_heating_level": {
        "name": "get_seat_heating_level",
        "description": "Query seat heating levels.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_seats_occupancy": {
        "name": "get_seats_occupancy",
        "description": "Query cabin seat occupancy.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_steering_wheel_heating_level": {
        "name": "get_steering_wheel_heating_level",
        "description": "Query steering wheel heating level.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_sunroof_and_sunshade_position": {
        "name": "get_sunroof_and_sunshade_position",
        "description": "Query sunroof and sunshade opening positions.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_temperature_inside_car": {
        "name": "get_temperature_inside_car",
        "description": "Query internal cabin temperature.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_trunk_door_position": {
        "name": "get_trunk_door_position",
        "description": "Query trunk door position.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_window_positions": {
        "name": "get_window_positions",
        "description": "Query opening percentage of all power windows.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "search_poi_at_location": {
        "name": "search_poi_at_location",
        "description": "Search points of interest near a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "category": {"type": "string"}
            },
            "required": ["location"]
        }
    },
    "search_poi_along_the_route": {
        "name": "search_poi_along_the_route",
        "description": "Search points of interest along an active navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "category_poi": {"type": "string"},
                "at_kilometer": {"type": "number"}
            },
            "required": ["category_poi"]
        }
    },
    "get_routes": {
        "name": "get_routes",
        "description": "Get routes between start location and destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_location": {"type": "string"},
                "destination": {"type": "string"}
            },
            "required": ["start_location", "destination"]
        }
    },
    "get_location_id_by_location_name": {
        "name": "get_location_id_by_location_name",
        "description": "Resolve location name to unique location ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "location_name": {"type": "string"}
            },
            "required": ["location_name"]
        }
    },
    "get_current_navigation_state": {
        "name": "get_current_navigation_state",
        "description": "Query current navigation state.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "convert_route_distance_into_time": {
        "name": "convert_route_distance_into_time",
        "description": "Convert driving distance into estimated travel time.",
        "parameters": {
            "type": "object",
            "properties": {
                "distance_km": {"type": "number"}
            },
            "required": ["distance_km"]
        }
    },
    "start_navigation": {
        "name": "start_navigation",
        "description": "Start navigation along a route.",
        "parameters": {
            "type": "object",
            "properties": {
                "route_id": {"type": "string"}
            },
            "required": ["route_id"]
        }
    },
    "stop_navigation": {
        "name": "stop_navigation",
        "description": "Stop current navigation session.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "set_destination": {
        "name": "set_destination",
        "description": "Set navigation destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"}
            },
            "required": ["destination"]
        }
    },
    "navigation_add_one_waypoint": {
        "name": "navigation_add_one_waypoint",
        "description": "Add one waypoint to active navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoint_location": {"type": "string"}
            },
            "required": ["waypoint_location"]
        }
    },
    "navigation_replace_one_waypoint": {
        "name": "navigation_replace_one_waypoint",
        "description": "Replace an existing waypoint in navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "old_waypoint": {"type": "string"},
                "new_waypoint": {"type": "string"}
            },
            "required": ["old_waypoint", "new_waypoint"]
        }
    },
    "navigation_replace_final_destination": {
        "name": "navigation_replace_final_destination",
        "description": "Replace final destination in navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "new_destination": {"type": "string"}
            },
            "required": ["new_destination"]
        }
    },
    "navigation_delete_one_waypoint": {
        "name": "navigation_delete_one_waypoint",
        "description": "Delete a waypoint from active navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoint_location": {"type": "string"}
            },
            "required": ["waypoint_location"]
        }
    },
    "navigation_delete_final_destination": {
        "name": "navigation_delete_final_destination",
        "description": "Delete final destination from active navigation route.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"}
            },
            "required": []
        }
    },
    "get_charging_status": {
        "name": "get_charging_status",
        "description": "Query EV battery state of charge (SOC) and max charging power.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_distance_by_soc": {
        "name": "get_distance_by_soc",
        "description": "Calculate remaining driving range given current SOC.",
        "parameters": {
            "type": "object",
            "properties": {
                "soc_percentage": {"type": "number"}
            },
            "required": ["soc_percentage"]
        }
    },
    "calculate_charging_time_by_soc": {
        "name": "calculate_charging_time_by_soc",
        "description": "Calculate required charging time to reach target SOC.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_soc": {"type": "number"}
            },
            "required": ["target_soc"]
        }
    },
    "calculate_charging_soc_by_time": {
        "name": "calculate_charging_soc_by_time",
        "description": "Calculate projected SOC after charging duration.",
        "parameters": {
            "type": "object",
            "properties": {
                "charging_time_minutes": {"type": "integer"}
            },
            "required": ["charging_time_minutes"]
        }
    },
    "get_contact_id_by_contact_name": {
        "name": "get_contact_id_by_contact_name",
        "description": "Search contact ID by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string"}
            },
            "required": ["contact_name"]
        }
    },
    "get_entries_from_calendar": {
        "name": "get_entries_from_calendar",
        "description": "Query calendar entries for current day.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    "get_contact_information": {
        "name": "get_contact_information",
        "description": "Query phone/email contact information by contact ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string"}
            },
            "required": ["contact_id"]
        }
    },
    "make_phone_call": {
        "name": "make_phone_call",
        "description": "Initiate a phone call to contact or number.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string"}
            },
            "required": ["phone_number"]
        }
    },
    "send_email": {
        "name": "send_email",
        "description": "Send an email message. REQUIRES USER CONFIRMATION.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_addresses": {"type": "array", "items": {"type": "string"}},
                "content_message": {"type": "string"}
            },
            "required": ["email_addresses", "content_message"]
        }
    },
    "calculate_math": {
        "name": "calculate_math",
        "description": "Execute mathematical calculations.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    },
    "calculate_date_time": {
        "name": "calculate_date_time",
        "description": "Perform date and time computations.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    },
    "think": {
        "name": "think",
        "description": "Scratchpad tool for internal reasoning step.",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {"type": "string"}
            },
            "required": ["thought"]
        }
    },
    "planning_tool": {
        "name": "planning_tool",
        "description": "Track multi-step task execution progress.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {"type": "string"}
            },
            "required": ["plan"]
        }
    },
    "get_weather": {
        "name": "get_weather",
        "description": "Query weather conditions for a location and time.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "time": {"type": "string"}
            },
            "required": ["location"]
        }
    },
    "get_user_preferences": {
        "name": "get_user_preferences",
        "description": "Retrieve stored user preferences (POI, climate, routing, settings).",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string"}
            },
            "required": []
        }
    }
}

CAR_BENCH_BASE_SYSTEM_PROMPT = """You are a helpful, precise in-car voice assistant capable of controlling vehicle settings, climate control, navigation, media, and productivity tools via function calls.

OPERATING PRINCIPLES & POLICIES:
1. LLM-POL:002 (Metric & Datetime): Use metric units (km, meters, °C) and 24-hour time format.
2. LLM-POL:004 (Safety Confirmation): Actions modifying external communications or critical vehicle entries (send_email, open_close_trunk_door, set_head_lights_high_beams) REQUIRE explicit user confirmation ("yes", "proceed") before execution.
3. AUT-POL:005 (Sunroof/Sunshade): Sunroof can only open if sunshade is open or opened in parallel.
4. LLM-POL:007 (AC Efficiency): Opening windows >25% while AC is ON requires warning the user about energy inefficiency.
5. AUT-POL:009 (Weather Constraints): Sunroof opening requires sunny/cloudy weather. Fog lights require stormy/hailing weather.
6. LLM-POL:010 (Disambiguation First): When a user request is ambiguous, check internal preferences (get_user_preferences) or vehicle status (get_vehicle_status) FIRST before asking the user.
7. LLM-POL:011 (Single Clarification): If internal preferences do not resolve ambiguity, ask the user ONE clarification question presenting clear, specific options.
8. LLM-POL:012 (No Re-confirmation): Once user confirms or selects an option, execute the action immediately without asking "are you sure?".
9. LLM-POL:015 (Removed Capability Refusal): If a tool or parameter is omitted from your available tools schema, politely refuse in 1 clear sentence without hallucinating fake tools or parameters.
10. LLM-POL:018 (No Schema Leakage): Never expose internal tool names (e.g. open_close_sunshade) or JSON syntax in natural language responses.

CURRENT VEHICLE CONTEXT:
- Location: {location}
- Date/Time: {datetime}
- Weather: {weather}
- Vehicle Speed: {speed} km/h
- Battery / Fuel: {soc}% State of Charge
"""

def generate_tool_call_id():
    return f"call_{uuid4().hex[:12]}"

def parse_actions(actions_field):
    if isinstance(actions_field, list):
        return actions_field
    if isinstance(actions_field, str):
        try:
            return json.loads(actions_field)
        except Exception:
            return []
    return []

def parse_json_field(field):
    if isinstance(field, (dict, list)):
        return field
    if isinstance(field, str):
        try:
            return json.loads(field)
        except Exception:
            return {}
    return {}

def format_system_prompt(context_init_config):
    context = parse_json_field(context_init_config)
    loc = context.get("current_location", {})
    loc_str = f"{loc.get('city', 'Stuttgart')}, {loc.get('country', 'Germany')}" if isinstance(loc, dict) else str(loc or "Stuttgart, Germany")
    dt_str = str(context.get("current_datetime", "2026-08-10 14:00"))
    weather = context.get("weather", {})
    weather_str = f"{weather.get('condition', 'Clear')}, {weather.get('temperature', 20)}°C" if isinstance(weather, dict) else str(weather or "Clear, 20°C")
    speed = context.get("speed", 0)
    soc = context.get("state_of_charge", 80)
    return CAR_BENCH_BASE_SYSTEM_PROMPT.format(
        location=loc_str,
        datetime=dt_str,
        weather=weather_str,
        speed=speed,
        soc=soc
    )

def build_tools_list_for_task(task_type, removed_part=None):
    tools_list = []
    for tool_name, tool_def in ALL_58_CAR_TOOLS.items():
        tools_list.append({
            "type": "function",
            "function": json.loads(json.dumps(tool_def))
        })
    if "hallucination" in str(task_type).lower() and removed_part:
        removals = parse_json_field(removed_part) if isinstance(removed_part, (list, dict, str)) else []
        if isinstance(removals, str):
            try:
                removals = json.loads(removals)
            except Exception:
                removals = [removals]
        pruned_list = []
        for tool_obj in tools_list:
            fn_name = tool_obj["function"]["name"]
            if fn_name in removals or any(r == fn_name for r in removals):
                continue
            param_removals = [r.split(".")[1] for r in removals if isinstance(r, str) and "." in r and r.split(".")[0] == fn_name]
            if param_removals:
                props = tool_obj["function"]["parameters"].get("properties", {})
                reqs = tool_obj["function"]["parameters"].get("required", [])
                for pr in param_removals:
                    props.pop(pr, None)
                    if pr in reqs:
                        reqs.remove(pr)
            pruned_list.append(tool_obj)
        return pruned_list if pruned_list else tools_list
    return tools_list

def generate_base_sample(task):
    sys_prompt = format_system_prompt(task.get("context_init_config"))
    tools = build_tools_list_for_task("base")
    actions = parse_actions(task.get("actions"))
    user_instruction = task.get("instruction", "Help me set vehicle features.")
    messages = [{"role": "system", "content": sys_prompt}]
    messages.append({"role": "user", "content": user_instruction})

    if not actions:
        messages.append({
            "role": "assistant",
            "content": "I'm ready to assist you. What would you like to set?"
        })
        return {
            "task_id": task.get("task_id", "base_sample"),
            "task_type": "base",
            "messages": messages,
            "tools": tools
        }

    # Group actions into sequential turns if dependencies exist
    has_dependencies = any(act.get("dependent_on_action_index") is not None for act in actions if isinstance(act, dict))

    if has_dependencies and len(actions) > 1:
        # Multi-turn sequential execution
        for act in actions:
            raw_t_name = act.get("name") or act.get("tool_name", "get_vehicle_status")
            t_name = normalize_tool_name(raw_t_name)
            t_kwargs = act.get("kwargs") or act.get("parameters", {})
            call_id = generate_tool_call_id()

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": t_name,
                        "arguments": json.dumps(t_kwargs)
                    }
                }]
            })
            
            # Dynamic mock result content
            mock_res = {"status": "success", "result": f"Executed {t_name}"}
            if "get_routes" in t_name:
                mock_res["routes"] = [{"route_id": t_kwargs.get("route_id", "route_1"), "distance_km": 12.5}]
            elif "search" in t_name:
                mock_res["pois"] = [{"id": "poi_1", "name": "Charging Station"}]
            elif "get_weather" in t_name:
                mock_res["weather"] = "Clear, 22°C"

            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(mock_res)
            })

        messages.append({
            "role": "assistant",
            "content": "I've completed your request to adjust the settings."
        })
    else:
        # Single-turn parallel tool call execution
        tool_calls = []
        tool_responses = []
        for act in actions:
            raw_t_name = act.get("name") or act.get("tool_name", "get_vehicle_status")
            t_name = normalize_tool_name(raw_t_name)
            t_kwargs = act.get("kwargs") or act.get("parameters", {})
            call_id = generate_tool_call_id()
            tool_calls.append({
                "id": call_id,
                "type": "function",
                "function": {
                    "name": t_name,
                    "arguments": json.dumps(t_kwargs)
                }
            })
            tool_responses.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps({"status": "success", "result": f"Executed {t_name}"})
            })
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        })
        messages.extend(tool_responses)
        messages.append({
            "role": "assistant",
            "content": "I've completed your request to adjust the settings."
        })

    return {
        "task_id": task.get("task_id", "base_sample"),
        "task_type": "base",
        "messages": messages,
        "tools": tools
    }

def generate_disambiguation_sample(task, variant="internal"):
    sys_prompt = format_system_prompt(task.get("context_init_config"))
    tools = build_tools_list_for_task("disambiguation")
    actions = parse_actions(task.get("actions"))
    instruction = task.get("instruction", "Adjust vehicle setting.")
    messages = [{"role": "system", "content": sys_prompt}]
    messages.append({"role": "user", "content": instruction})
    target_action = actions[0] if actions else {"name": "open_close_sunshade", "kwargs": {"action": "open", "sunshade": "front", "percentage": 60}}
    raw_target_name = target_action.get("name") or target_action.get("tool_name", "open_close_sunshade")
    target_name = normalize_tool_name(raw_target_name)
    target_kwargs = target_action.get("kwargs") or target_action.get("parameters", {})
    pref_call_id = generate_tool_call_id()
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": pref_call_id,
            "type": "function",
            "function": {
                "name": "get_user_preferences",
                "arguments": json.dumps({"category": "vehicle_settings"})
            }
        }]
    })
    if variant == "internal":
        messages.append({
            "role": "tool",
            "tool_call_id": pref_call_id,
            "content": json.dumps({"status": "success", "preferences": target_kwargs})
        })
        target_call_id = generate_tool_call_id()
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": target_call_id,
                "type": "function",
                "function": {
                    "name": target_name,
                    "arguments": json.dumps(target_kwargs)
                }
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": target_call_id,
            "content": json.dumps({"status": "success"})
        })
        messages.append({
            "role": "assistant",
            "content": f"Based on your stored preferences, I've adjusted the {target_name.replace('_', ' ')} for you."
        })
    else:
        messages.append({
            "role": "tool",
            "tool_call_id": pref_call_id,
            "content": json.dumps({"status": "success", "preferences": {}, "message": "No matching preferences"})
        })
        param_desc = ", ".join(f"{k} ({v})" for k, v in target_kwargs.items())
        messages.append({
            "role": "assistant",
            "content": f"To make sure I set this right, could you clarify your preferred setting ({param_desc})?"
        })
        messages.append({
            "role": "user",
            "content": f"Please set it with {param_desc}."
        })
        target_call_id = generate_tool_call_id()
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": target_call_id,
                "type": "function",
                "function": {
                    "name": target_name,
                    "arguments": json.dumps(target_kwargs)
                }
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": target_call_id,
            "content": json.dumps({"status": "success"})
        })
        messages.append({
            "role": "assistant",
            "content": f"I've updated the {target_name.replace('_', ' ')} as requested."
        })
    return {
        "task_id": task.get("task_id", "disambig_sample"),
        "task_type": "disambiguation",
        "messages": messages,
        "tools": tools
    }

USER_QUERY_TEMPLATES = [
    "Can you adjust the {feature} for me?",
    "Please turn on the {feature}.",
    "Could you set the {feature} right now?",
    "I'd like to adjust the {feature}, please.",
    "Can you change the {feature} settings?",
    "Please activate the {feature} for me.",
    "Would you mind setting the {feature}?",
    "Can we turn the {feature} on?"
]

REFUSAL_RESPONSE_TEMPLATES = [
    "I'm sorry, but controlling {feature} is currently not available in this vehicle configuration. Is there anything else I can help you adjust?",
    "I apologize, but I don't have access to the {feature} controls right now. How else can I assist you?",
    "I'm afraid the {feature} functionality is not supported in this vehicle setup. Would you like me to adjust something else?",
    "Unfortunately, the {feature} feature is disabled or unavailable at the moment. Can I help you with another setting?",
    "I cannot perform adjustments on {feature} as that capability is missing. Please let me know if you need help with other features."
]

RECOVERY_USER_TEMPLATES = [
    ("Okay, then can you set the temperature to {temp} degrees instead?", "set_temperature", {"temperature": 21, "zone": "all"}, "I've set the cabin temperature to {temp}°C for all zones."),
    ("Alright, please set the seat heating to level {level} instead.", "set_seat_heating", {"level": 2, "seat": "driver"}, "I've turned on the driver's seat heating to level {level}."),
    ("Fair enough, could you set the ambient light to {color}?", "set_ambient_lighting", {"color": "blue", "brightness": 80}, "I've set the interior ambient lighting to {color}."),
    ("Never mind, please check the current battery status.", "get_charging_status", {}, "The current battery state of charge is 78%.")
]

def generate_hallucination_sample(task):
    removed_part = task.get("removed_part")
    sys_prompt = format_system_prompt(task.get("context_init_config"))
    tools = build_tools_list_for_task("hallucination", removed_part)
    instruction = task.get("instruction", "Use unavailable vehicle feature.")
    persona = task.get("persona", "")
    feature_match = re.search(r"tool\s+([a-zA-Z0-9_]+)", persona)
    removed_name = feature_match.group(1) if feature_match else "this setting"
    feature_desc = normalize_tool_name(removed_name).replace("_", " ")

    query_tmpl = random.choice(USER_QUERY_TEMPLATES)
    refusal_tmpl = random.choice(REFUSAL_RESPONSE_TEMPLATES)

    messages = [{"role": "system", "content": sys_prompt}]
    messages.append({"role": "user", "content": query_tmpl.format(feature=feature_desc)})
    messages.append({"role": "assistant", "content": refusal_tmpl.format(feature=feature_desc)})

    if random.random() < 0.4:
        rec_prompt, rec_tool, rec_args, rec_res = random.choice(RECOVERY_USER_TEMPLATES)
        temp_val = random.choice([20, 21, 22])
        level_val = random.choice([1, 2, 3])
        color_val = random.choice(["blue", "warm white", "cyan"])
        
        prompt_text = rec_prompt.format(temp=temp_val, level=level_val, color=color_val)
        res_text = rec_res.format(temp=temp_val, level=level_val, color=color_val)
        
        # Adjust args
        args = dict(rec_args)
        if "temperature" in args: args["temperature"] = temp_val
        if "level" in args: args["level"] = level_val
        if "color" in args: args["color"] = color_val

        messages.append({"role": "user", "content": prompt_text})
        call_id = generate_tool_call_id()
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": call_id,
                "type": "function",
                "function": {
                    "name": rec_tool,
                    "arguments": json.dumps(args)
                }
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps({"status": "success"})
        })
        messages.append({
            "role": "assistant",
            "content": res_text
        })
    return {
        "task_id": task.get("task_id", "hallu_sample"),
        "task_type": "hallucination",
        "messages": messages,
        "tools": tools
    }

def generate_confirmation_sample(task):
    sys_prompt = format_system_prompt(task.get("context_init_config"))
    tools = build_tools_list_for_task("base")
    messages = [{"role": "system", "content": sys_prompt}]
    messages.append({"role": "user", "content": "Open the trunk door please."})
    messages.append({
        "role": "assistant",
        "content": "Opening the trunk door while the vehicle is parked requires your confirmation. Would you like me to proceed?"
    })
    messages.append({"role": "user", "content": "Yes, go ahead and open it."})
    call_id = generate_tool_call_id()
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {
                "name": "open_close_trunk_door",
                "arguments": json.dumps({"action": "open"})
            }
        }]
    })
    messages.append({
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps({"status": "success"})
    })
    messages.append({
        "role": "assistant",
        "content": "I've opened the trunk door for you."
    })
    return {
        "task_id": task.get("task_id", "confirm_sample"),
        "task_type": "confirmation",
        "messages": messages,
        "tools": tools
    }

def load_raw_tasks(file_path):
    tasks = []
    if not os.path.exists(file_path):
        return tasks
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except Exception:
                    pass
    return tasks

def validate_sample(sample):
    assert "messages" in sample and isinstance(sample["messages"], list), "Missing messages list"
    assert "tools" in sample and isinstance(sample["tools"], list), "Missing tools list"
    assert len(sample["tools"]) > 0, "Tools array is empty!"
    for msg in sample["messages"]:
        assert "role" in msg, "Message missing role"
        assert msg["role"] in ["system", "user", "assistant", "tool"], f"Invalid role {msg['role']}"
        if msg["role"] == "assistant" and "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                norm_fn = normalize_tool_name(fn_name)
                assert norm_fn in ALL_58_CAR_TOOLS, f"Invalid tool name: {fn_name}"
    return True

import urllib.request
import urllib.error

def call_openai_vllm_api(messages, tools, api_base, api_key, model):
    """
    Call an OpenAI-compatible API endpoint (vLLM local server or OpenAI API).
    Uses standard library urllib.request to avoid external dependency requirements.
    """
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key or 'EMPTY'}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    if tools:
        payload["tools"] = tools

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            choice = res_json["choices"][0]["message"]
            return choice
    except Exception as e:
        print(f"[API WARN] Failed to call API ({url}): {e}")
        return None

def generate_base_sample_api(task, api_base, api_key, model):
    """Generates a Base sample using online vLLM/OpenAI API backend."""
    sys_prompt = format_system_prompt(task.get("context_init_config"))
    tools = build_tools_list_for_task("base")
    user_instruction = task.get("instruction", "Help me set vehicle features.")
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_instruction}
    ]
    
    response = call_openai_vllm_api(messages, tools, api_base, api_key, model)
    if not response:
        return generate_base_sample(task)

    assistant_msg = {"role": "assistant", "content": response.get("content")}
    tool_calls = response.get("tool_calls")
    if tool_calls:
        assistant_msg["tool_calls"] = tool_calls
    messages.append(assistant_msg)

    if tool_calls:
        for tc in tool_calls:
            call_id = tc.get("id", generate_tool_call_id())
            fn_name = tc.get("function", {}).get("name", "get_vehicle_status")
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps({"status": "success", "result": f"Executed {fn_name}"})
            })
        second_response = call_openai_vllm_api(messages, None, api_base, api_key, model)
        if second_response and second_response.get("content"):
            messages.append({"role": "assistant", "content": second_response.get("content")})
        else:
            messages.append({"role": "assistant", "content": "I've completed your request."})

    return {
        "task_id": task.get("task_id", "base_sample"),
        "task_type": "base",
        "messages": messages,
        "tools": tools
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CAR-Bench SFT Training Data Generator")
    parser.add_argument("--mode", choices=["simulated", "api"], default="simulated",
                        help="Data generation mode: 'simulated' (0-cost offline rule-based engine) or 'api' (online vLLM/OpenAI API model generation)")
    parser.add_argument("--api-base", default=os.environ.get("OPENAI_API_BASE", "http://localhost:8000/v1"),
                        help="OpenAI-compatible API base URL (default: http://localhost:8000/v1 for local vLLM server)")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "EMPTY"),
                        help="API key for vLLM or OpenAI endpoint")
    parser.add_argument("--model", default=os.environ.get("CAR_BENCH_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                        help="Model name for API generation (default: Qwen/Qwen2.5-7B-Instruct)")
    args = parser.parse_args()

    print(f"[INFO] Running CAR-Bench Data Generator in '{args.mode.upper()}' mode...")
    if args.mode == "api":
        print(f"       API Base: {args.api_base} | Model: {args.model}")

    data_dir = os.path.dirname(os.path.abspath(__file__))
    task_files = {
        "base": [
            os.path.join(data_dir, "raw_tasks_base_train.jsonl"),
            os.path.join(data_dir, "raw_tasks_base_test.jsonl")
        ],
        "disambiguation": [
            os.path.join(data_dir, "raw_tasks_disambiguation_train.jsonl"),
            os.path.join(data_dir, "raw_tasks_disambiguation_test.jsonl")
        ],
        "hallucination": [
            os.path.join(data_dir, "raw_tasks_hallucination_train.jsonl"),
            os.path.join(data_dir, "raw_tasks_hallucination_test.jsonl")
        ]
    }
    all_samples = []
    base_samples = []
    disambig_samples = []
    hallu_samples = []

    # 1. Process Base Tasks (~2,550 samples)
    for fp in task_files["base"]:
        tasks = load_raw_tasks(fp)
        for t in tasks:
            for _ in range(25):
                if args.mode == "api":
                    s = generate_base_sample_api(t, args.api_base, args.api_key, args.model)
                else:
                    s = generate_base_sample(t)
                if validate_sample(s):
                    base_samples.append(s)
                    all_samples.append(s)

    # 2. Process Safety Confirmation Tasks (~500 samples)
    for fp in task_files["base"]:
        tasks = load_raw_tasks(fp)
        for t in tasks[:25]:
            for _ in range(20):
                s = generate_confirmation_sample(t)
                if validate_sample(s):
                    base_samples.append(s)
                    all_samples.append(s)

    # 3. Process Disambiguation Tasks (~2,610 samples)
    for fp in task_files["disambiguation"]:
        tasks = load_raw_tasks(fp)
        for t in tasks:
            for _ in range(45):
                var = "internal" if random.random() < 0.6 else "external"
                s = generate_disambiguation_sample(t, variant=var)
                if validate_sample(s):
                    disambig_samples.append(s)
                    all_samples.append(s)

    # 4. Process Hallucination Tasks (~2,600 samples)
    for fp in task_files["hallucination"]:
        tasks = load_raw_tasks(fp)
        for t in tasks:
            for _ in range(26):
                s = generate_hallucination_sample(t)
                if validate_sample(s):
                    hallu_samples.append(s)
                    all_samples.append(s)

    output_all = os.path.join(data_dir, "car_sft_dataset_openai.jsonl")
    output_dis = os.path.join(data_dir, "car_disambiguation_sft.jsonl")
    output_hal = os.path.join(data_dir, "car_hallucination_sft.jsonl")
    output_bas = os.path.join(data_dir, "car_base_sft.jsonl")

    for path, data in [
        (output_all, all_samples),
        (output_dis, disambig_samples),
        (output_hal, hallu_samples),
        (output_bas, base_samples)
    ]:
        with open(path, "w", encoding="utf-8") as f:
            for s in data:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"[SUCCESS] Generated Total In-Domain Samples : {len(all_samples)}")
    print(f"  - Base / Confirmation SFT Samples        : {len(base_samples)} -> {output_bas}")
    print(f"  - Disambiguation SFT Samples             : {len(disambig_samples)} -> {output_dis}")
    print(f"  - Hallucination SFT Samples              : {len(hallu_samples)} -> {output_hal}")
    print(f"  - Combined Master SFT Dataset            : {len(all_samples)} -> {output_all}")

if __name__ == "__main__":
    main()
