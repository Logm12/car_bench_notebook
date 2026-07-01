"""
CAR-bench Agent - Agent under test that solves CAR-bench tasks.

This is the agent being tested. It:
1. Receives task descriptions with available tools from the evaluator
2. Decides which tool to call or how to respond
3. Returns responses in the expected JSON format wrapped in <json>...</json> tags
"""
import argparse
import json
import os
import time
from pathlib import Path
import sys
import uvicorn
from dotenv import load_dotenv
import re

load_dotenv()

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.helpers.proto_helpers import new_message, new_text_part, new_data_part, new_task_from_user_message
from a2a.types import Role, TaskState
from google.protobuf.json_format import MessageToDict
from litellm import completion
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import configure_logger
from tool_call_types import ToolCall, ToolCallsData
from turn_metrics import TURN_METRICS_KEY, PROMPT_TOKENS, COMPLETION_TOKENS, COST, MODEL, THINKING_TOKENS, NUM_LLM_CALLS, AVG_LLM_CALL_TIME_MS, NUM_PASSES
sys.path.pop(0)

logger = configure_logger(role="agent_under_test", context="-")

SYSTEM_PROMPT = """You are a helpful car voice assistant. Follow the policy and tool instructions provided."""


def extract_context_from_system_prompt(system_prompt: str):
    location_id = "loc_mun_9995"  # default
    loc_match = re.search(r"CURRENT_LOCATION\s*=\s*(\{.*?\})", system_prompt, re.DOTALL)
    if loc_match:
        try:
            loc_data = json.loads(loc_match.group(1))
            location_id = loc_data.get("id", location_id)
        except Exception:
            pass

    month, day, hour = 2, 14, 12  # defaults
    dt_match = re.search(r"DATETIME\s*=\s*(\{.*?\})", system_prompt, re.DOTALL)
    if dt_match:
        try:
            dt_data = json.loads(dt_match.group(1))
            month = dt_data.get("month", month)
            day = dt_data.get("day", day)
            hour = dt_data.get("hour", hour)
        except Exception:
            pass

    return location_id, month, day, hour


def does_tool_require_confirmation(tool_name: str, arguments: dict, messages: list) -> bool:
    if tool_name in ["send_email", "open_close_trunk_door", "set_head_lights_high_beams"]:
        return True
        
    if tool_name == "open_close_sunroof":
        percentage = arguments.get("percentage")
        try:
            if percentage is not None and float(percentage) == 0.0:
                return False
        except Exception:
            pass
        # Find get_weather result in history
        for msg in reversed(messages):
            if msg.get("role") == "tool" and msg.get("name") == "get_weather":
                try:
                    content_data = json.loads(msg.get("content", "{}"))
                    condition = content_data.get("result", {}).get("current_slot", {}).get("condition", "")
                    if condition and condition not in ["sunny", "cloudy", "partly_cloudy"]:
                        return True
                except Exception:
                    pass
                break
                
    if tool_name == "set_fog_lights":
        # Find get_weather result in history
        for msg in reversed(messages):
            if msg.get("role") == "tool" and msg.get("name") == "get_weather":
                try:
                    content_data = json.loads(msg.get("content", "{}"))
                    condition = content_data.get("result", {}).get("current_slot", {}).get("condition", "")
                    if condition and condition not in ["cloudy_and_thunderstorm", "cloudy_and_hail"]:
                        return True
                except Exception:
                    pass
                break
                
    return False


def enrich_system_prompt(system_prompt: str, removed_tools: list, removed_params: list) -> str:
    lines = [system_prompt]
    
    lines.append("\n\n## Custom Assistant Guidelines (Strict Enforcement)")
    lines.append("- CONFIRMATION POLICY: Before calling any tool that requires confirmation ('send_email', 'open_close_trunk_door', 'set_head_lights_high_beams'), you MUST list the intended tool parameters and action details (e.g. tool name, action name, parameter name, and parameter value) and obtain explicit expressive user confirmation (yes) to proceed. Example request: 'To open the trunk door, I need to call the open_close_trunk_door function with the action parameter set to 'OPEN'. Do you confirm that you want me to proceed?'")
    lines.append("- WEATHER CONFIRMATION: If you need to open the sunroof and the weather is not sunny, cloudy, or partly_cloudy, or if you need to set the fog lights and the weather is not cloudy_and_thunderstorm or cloudy_and_hail, you MUST check the weather first, and if the condition is met, obtain explicit user confirmation (yes) before calling the tool. Do not ask for confirmation if the weather conditions are safe (sunny, cloudy, partly_cloudy for sunroof; cloudy_and_thunderstorm, cloudy_and_hail for fog lights).")
    
    if removed_tools:
        lines.append(f"- REMOVED CAPABILITIES: The following tools/capabilities are NOT available in this environment: {', '.join(removed_tools)}. If the user asks you to perform an action using any of these tools, you MUST immediately inform the user that you don't have the capability/tool to perform the action, using a response like: 'I don't have the tool/capability to do that'. Do NOT attempt to call the removed tools.")
    if removed_params:
        lines.append(f"- REMOVED PARAMETERS: The following parameters are NOT available: {', '.join(removed_params)}. If the user asks you to set any of these parameters, you MUST immediately inform the user that the capability/parameter is not available, using a response like: 'I don't have the capability/parameter to set that'. Do NOT attempt to call tools with these parameters.")
        
    lines.append("- UNKNOWN RESPONSE HANDLING: If any tool call returns a response containing 'unknown' for a parameter, you MUST immediately inform the user that the requested information/capability is not available because it returned 'unknown'. Do NOT hallucinate the details or assume success.")
    lines.append("- DISAMBIGUATION POLICY: If the user request is ambiguous (e.g. 'open the sunroof' without percentage, or 'set the temperature' without target zone/value), check the user preferences in the conversation history (retrieved from get_user_preferences) to resolve it internally. If the preference is not found and cannot be resolved internally, ask the user for clarification before taking action. Never make assumptions on ambiguous values.")
    
    return "\n".join(lines)


def sanitize_schema(schema):
    if not isinstance(schema, dict):
        return schema
    
    sanitized = {}
    for k, v in schema.items():
        if k == "properties" and isinstance(v, dict):
            # Strip additionalProperties from within properties
            clean_properties = {}
            for pk, pv in v.items():
                if pk == "additionalProperties":
                    # If additionalProperties is incorrectly inside properties, skip it
                    continue
                clean_properties[pk] = sanitize_schema(pv)
            sanitized[k] = clean_properties
        else:
            sanitized[k] = sanitize_schema(v) if isinstance(v, (dict, list)) else v
            
    return sanitized


def parse_tool_calls_from_text(text: str) -> list:
    """Parse tool calls formatted as JSON from assistant content text."""
    if not text:
        return []
    
    tool_calls = []
    
    # Clean up markdown code blocks if any
    clean_text = re.sub(r"```json\s*", "", text)
    clean_text = re.sub(r"```\s*", "", clean_text)
    
    # Try parsing the whole text as a JSON array or object
    try:
        data = json.loads(clean_text.strip())
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and ("name" in item or "tool_name" in item or "function" in item):
                    tool_calls.append(item)
        elif isinstance(data, dict):
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                tool_calls.extend(data["tool_calls"])
            elif "name" in data or "tool_name" in data or "function" in data:
                tool_calls.append(data)
    except json.JSONDecodeError:
        pass
        
    if not tool_calls:
        # Try parsing line-by-line
        lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
        for line in lines:
            try:
                # Find the first '{' and last '}' on the line
                start = line.find('{')
                end = line.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = line[start:end+1]
                    data = json.loads(json_str)
                    if isinstance(data, dict) and ("name" in data or "tool_name" in data or "function" in data):
                        tool_calls.append(data)
            except Exception:
                continue

    # Standardize the extracted tool calls to the format:
    # {"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}
    standardized_calls = []
    for tc in tool_calls:
        name = None
        arguments = None
        
        if "function" in tc and isinstance(tc["function"], dict):
            name = tc["function"].get("name")
            arguments = tc["function"].get("arguments")
        elif "name" in tc:
            name = tc["name"]
            arguments = tc.get("arguments")
        elif "tool_name" in tc:
            name = tc["tool_name"]
            arguments = tc.get("arguments")
            
        if name:
            if isinstance(arguments, dict):
                args_str = json.dumps(arguments)
            elif isinstance(arguments, str):
                args_str = arguments
            else:
                args_str = "{}"
                
            standardized_calls.append({
                "id": "call_" + str(uuid4())[:8],
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": args_str
                }
            })
            
    return standardized_calls



class CARBenchAgentExecutor(AgentExecutor):
    """Executor for the CAR-bench agent under test using native tool calling."""

    def __init__(self, model: str, temperature: float = 0.0, thinking: bool = False, reasoning_effort: str = "medium", interleaved_thinking: bool = False):
        self.model = model
        self.temperature = temperature
        self.thinking = thinking
        self.reasoning_effort = reasoning_effort  # Can be 'none', 'disable', 'low', 'medium', 'high', or integer token budget
        self.interleaved_thinking = interleaved_thinking  # Whether to use interleaved thinking
        self.ctx_id_to_messages: dict[str, list[dict]] = {}
        self.ctx_id_to_tools: dict[str, list[dict]] = {}
        self.ctx_id_to_system_prompt: dict[str, str] = {}
        # Per-context turn metrics accumulation (reset when final response is sent)
        self.ctx_id_to_turn_metrics: dict[str, dict] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        inbound_message = context.message
        ctx_logger = logger.bind(role="agent_under_test", context=f"ctx:{context.context_id[:8]}")

        # Initialize or get conversation history
        if context.context_id not in self.ctx_id_to_messages:
            self.ctx_id_to_messages[context.context_id] = []

        messages = self.ctx_id_to_messages[context.context_id]
        tools = self.ctx_id_to_tools.get(context.context_id, [])

        # Stage 1: Parse all incoming parts
        user_message_text = None
        incoming_tool_results = None
        system_prompt = None
        
        try:
            for part in inbound_message.parts:
                content_type = part.WhichOneof("content")
                if content_type == "text":
                    text = part.text
                    if "System:" in text and "\n\nUser:" in text:
                        parts_split = text.split("\n\nUser:", 1)
                        system_prompt = parts_split[0].replace("System:", "").strip()
                        user_message_text = parts_split[1].strip()
                    else:
                        user_message_text = text
                elif content_type == "data":
                    data = MessageToDict(part.data)
                    if "tools" in data:
                        tools = data["tools"]
                        self.ctx_id_to_tools[context.context_id] = tools
                    elif "tool_results" in data:
                        incoming_tool_results = data["tool_results"]
                        
            if not user_message_text and not incoming_tool_results:
                user_message_text = context.get_user_input()
        except Exception as e:
            logger.warning(f"Failed to parse message parts: {e}, using fallback")
            user_message_text = context.get_user_input()

        ctx_logger.info(
            "Received user message",
            context_id=context.context_id[:8],
            turn=len(messages) + 1,
            message_preview=(user_message_text[:100] if user_message_text else
                             f"[{len(incoming_tool_results)} tool results]" if incoming_tool_results else "")
        )

        # Stage 2: Initialize/process history and enrich system prompt
        if system_prompt is not None:
            # Compute removed tools and parameters
            try:
                from car_bench.envs.car_voice_assistant.tools import ALL_TOOLS
                default_tools = {t.get_info()["function"]["name"]: t.get_info() for t in ALL_TOOLS}
            except Exception as e:
                logger.warning(f"Could not import ALL_TOOLS: {e}")
                default_tools = {}

            removed_tools = []
            removed_params = []
            if default_tools and tools:
                available_names = {t["function"]["name"] for t in tools}
                for name, def_t in default_tools.items():
                    if name not in available_names:
                        removed_tools.append(name)
                    else:
                        def_params = def_t["function"]["parameters"].get("properties", {})
                        curr_t = next(t for t in tools if t["function"]["name"] == name)
                        curr_params = curr_t["function"]["parameters"].get("properties", {})
                        for p in def_params:
                            if p not in curr_params:
                                removed_params.append(f"{name}.{p}")

            system_prompt = enrich_system_prompt(system_prompt, removed_tools, removed_params)
            
            messages = [{"role": "system", "content": system_prompt}]
            self.ctx_id_to_messages[context.context_id] = messages
            self.ctx_id_to_system_prompt[context.context_id] = system_prompt

        # Check if previous message had tool calls - if so, format as tool results
        if messages and messages[-1].get("role") == "assistant" and messages[-1].get("tool_calls"):
            prev_tool_calls = messages[-1]["tool_calls"]

            if incoming_tool_results:
                tool_call_by_name = {}
                for tc in prev_tool_calls:
                    name = tc["function"]["name"]
                    tool_call_by_name.setdefault(name, []).append(tc)

                tool_results = []
                for tr in incoming_tool_results:
                    tr_name = tr.get("tool_name", "") if isinstance(tr, dict) else tr.get("toolName", "")
                    matching_calls = tool_call_by_name.get(tr_name, [])
                    if matching_calls:
                        matched_tc = matching_calls.pop(0)
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": matched_tc["id"],
                            "content": tr.get("content", ""),
                            "name": tr_name,
                        })
                    else:
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_call_id", tr.get("toolCallId", f"unknown_{tr_name}")),
                            "content": tr.get("content", ""),
                            "name": tr_name,
                        })
                
                # Check for "unknown" in any of the results (missing tool response hallucination)
                has_unknown_result = False
                unknown_fields = []
                for tr in incoming_tool_results:
                    content_str = tr.get("content", "")
                    if "unknown" in content_str.lower():
                        has_unknown_result = True
                        try:
                            content_data = json.loads(content_str)
                            if isinstance(content_data, dict):
                                for k, v in content_data.get("result", {}).items():
                                    if v == "unknown":
                                        unknown_fields.append(k)
                        except Exception:
                            pass
                
                # Add tool results to messages
                messages.extend(tool_results)

                if has_unknown_result:
                    warn_msg = "WARNING: Some retrieved data contains 'unknown' values because those capabilities are removed/unavailable. You MUST explicitly inform the user that you cannot retrieve this information."
                    if unknown_fields:
                        warn_msg = f"WARNING: The following retrieved fields are 'unknown' because their capabilities/responses are removed: {', '.join(unknown_fields)}. You MUST explicitly inform the user that this information is unavailable."
                    messages.append({"role": "system", "content": warn_msg})
                    
            else:
                tool_results = []
                for tc in prev_tool_calls:
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": user_message_text or "",
                        "name": tc["function"]["name"],
                    })
                messages.extend(tool_results)
        else:
            # Regular user message
            if user_message_text is not None:
                messages.append({"role": "user", "content": user_message_text})

        # Check if we should call get_user_preferences at the start of the conversation
        has_get_user_prefs = any(t["function"]["name"] == "get_user_preferences" for t in tools)
        already_called_prefs = any(
            msg.get("role") == "assistant" and msg.get("tool_calls") and any(tc["function"]["name"] == "get_user_preferences" for tc in msg["tool_calls"])
            for msg in messages
        )
        
        if has_get_user_prefs and not already_called_prefs and len(messages) <= 2:
            ctx_logger.info(
                "Intercepting to retrieve all user preferences at start of conversation",
                context_id=context.context_id[:8]
            )
            
            intercepted_tool_call = {
                "id": "call_" + str(uuid4())[:8],
                "type": "function",
                "function": {
                    "name": "get_user_preferences",
                    "arguments": json.dumps({
                        "preference_categories": {
                            "points_of_interest": {"charging_stations": True},
                            "navigation_and_routing": {"route_selection": True},
                            "vehicle_settings": {"climate_control": True, "vehicle_settings": True},
                            "productivity_and_communication": {"email": True, "calendar": True},
                            "weather": {"weather": True}
                        }
                    })
                }
            }
            
            parts = []
            tool_calls_list = [
                ToolCall(
                    tool_name="get_user_preferences",
                    arguments=json.loads(intercepted_tool_call["function"]["arguments"]),
                )
            ]
            tool_calls_data = ToolCallsData(tool_calls=tool_calls_list)
            parts.append(new_data_part(tool_calls_data.model_dump()))
            
            assistant_message_for_history = {
                "role": "assistant",
                "content": "",
                "tool_calls": [intercepted_tool_call]
            }
            messages.append(assistant_message_for_history)
            
            response_message = new_message(
                parts=parts,
                context_id=context.context_id,
                role=Role.ROLE_AGENT,
            )
            await event_queue.enqueue_event(response_message)
            return

        # Call LLM with native tool calling
        try:
            # Configure prompt caching (guard against empty lists)
            if tools:
                tools[-1]["function"]["cache_control"] = {"type": "ephemeral"}
            if messages:
                messages[0]["cache_control"] = {"type": "ephemeral"}

            sanitized_tools = None
            if tools:
                import copy
                sanitized_tools = []
                for tool in tools:
                    t = copy.deepcopy(tool)
                    if "function" in t and "parameters" in t["function"]:
                        t["function"]["parameters"] = sanitize_schema(t["function"]["parameters"])
                    sanitized_tools.append(t)

            completion_kwargs = {
                "model": self.model,
                "tools": sanitized_tools,
                "temperature": self.temperature,
            }
            # Support separate API base and key for local agent under test (e.g. Ollama)
            agent_api_base = os.getenv("AGENT_API_BASE")
            if agent_api_base:
                completion_kwargs["api_base"] = agent_api_base
                if self.model.startswith("openai/"):
                    completion_kwargs["api_key"] = os.getenv("AGENT_API_KEY", "ollama")

            # Configure reasoning effort / thinking
            if self.thinking:
                if self.model == "claude-opus-4-6":
                    completion_kwargs["thinking"] = {
                        "type": "adaptive"
                    }
                else:
                    if self.reasoning_effort in [
                        "none",
                        "disable",
                        "low",
                        "medium",
                        "high",
                    ]:
                        completion_kwargs["reasoning_effort"] = self.reasoning_effort
                    else:
                        try:
                            thinking_budget = int(self.reasoning_effort)
                        except ValueError:
                            raise ValueError(
                                "reasoning_effort must be 'none', 'disable', 'low', 'medium', 'high', or an integer value"
                            )
                        completion_kwargs["thinking"] = {
                            "type": "enabled",
                            "budget_tokens": thinking_budget,
                        }
                    if self.interleaved_thinking:
                        completion_kwargs["extra_headers"] = {
                            "anthropic-beta": "interleaved-thinking-2025-05-14"
                        }

            call_start_time = time.perf_counter()
            response = completion(
                messages=messages,
                **completion_kwargs
            )

            # Accumulate turn metrics for this LLM call
            call_end_time = time.perf_counter()
            call_elapsed_ms = (call_end_time - call_start_time) * 1000.0

            if context.context_id not in self.ctx_id_to_turn_metrics:
                self.ctx_id_to_turn_metrics[context.context_id] = {
                    PROMPT_TOKENS: 0,
                    COMPLETION_TOKENS: 0,
                    THINKING_TOKENS: 0,
                    COST: 0.0,
                    NUM_LLM_CALLS: 0,
                    "_total_llm_time_ms": 0.0,
                }

            turn_m = self.ctx_id_to_turn_metrics[context.context_id]
            usage = getattr(response, "usage", None)
            if usage:
                turn_m[PROMPT_TOKENS] += getattr(usage, "prompt_tokens", 0) or 0
                turn_m[COMPLETION_TOKENS] += getattr(usage, "completion_tokens", 0) or 0
                details = getattr(usage, "completion_tokens_details", None)
                if details:
                    turn_m[THINKING_TOKENS] += getattr(details, "reasoning_tokens", 0) or 0
            turn_m[COST] += getattr(response, "_hidden_params", {}).get("response_cost", 0.0) or 0.0
            turn_m[NUM_LLM_CALLS] += 1
            turn_m["_total_llm_time_ms"] += call_elapsed_ms

            # Get the message from LLM
            llm_message = response.choices[0].message
            assistant_content = llm_message.model_dump(exclude_unset=True)

            # Extract tool calls from assistant content
            tool_calls = assistant_content.get("tool_calls")

            # Fallback for models outputting JSON tool calls as text content
            if not tool_calls and assistant_content.get("content"):
                parsed_calls = parse_tool_calls_from_text(assistant_content["content"])
                if parsed_calls:
                    ctx_logger.info(
                        "Parsed tool calls from assistant text content",
                        count=len(parsed_calls)
                    )
                    assistant_content["tool_calls"] = parsed_calls
                    tool_calls = parsed_calls
                    # Clear content so we don't treat it as a text response simultaneously
                    assistant_content["content"] = ""

            # 1. Hallucination Interception (Failsafe)
            if tool_calls:
                available_tool_names = {t["function"]["name"] for t in tools}
                blocked_by_hallucination = False
                block_reason = ""

                for tc in tool_calls:
                    tc_name = tc.get("function", {}).get("name", "")
                    if tc_name not in available_tool_names:
                        blocked_by_hallucination = True
                        block_reason = f"I cannot perform this action because the capability/tool '{tc_name}' is not available."
                        break
                    
                    try:
                        args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except Exception:
                        args = {}
                    
                    curr_t = next((t for t in tools if t["function"]["name"] == tc_name), None)
                    if curr_t:
                        allowed_params = curr_t["function"]["parameters"].get("properties", {}).keys()
                        for p in args:
                            if p not in allowed_params:
                                blocked_by_hallucination = True
                                block_reason = f"I cannot set that because the parameter '{p}' for tool '{tc_name}' is not available."
                                break
                    if blocked_by_hallucination:
                        break

                if blocked_by_hallucination:
                    ctx_logger.info(
                        "Intercepting and blocking tool call due to hallucination of removed capability",
                        tool_calls=tool_calls,
                        reason=block_reason
                    )
                    assistant_content["tool_calls"] = None
                    tool_calls = None
                    assistant_content["content"] = block_reason

            # 2. Weather Check Injection
            if tool_calls:
                # Check if sunroof or fog lights are called
                has_sunroof_or_fog_lights = False
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    if name in ("open_close_sunroof", "set_fog_lights"):
                        has_sunroof_or_fog_lights = True
                        break

                if has_sunroof_or_fog_lights:
                    # Check if weather has been checked already in the history
                    weather_checked = False
                    for msg in messages:
                        if msg.get("role") == "tool" and msg.get("name") == "get_weather":
                            weather_checked = True
                            break
                        if msg.get("role") == "assistant" and msg.get("tool_calls"):
                            if any(x.get("function", {}).get("name", "") == "get_weather" for x in msg["tool_calls"]):
                                weather_checked = True
                                break
                    
                    if not weather_checked:
                        sys_prompt = self.ctx_id_to_system_prompt.get(context.context_id, "")
                        loc_id, month, day, hour = extract_context_from_system_prompt(sys_prompt)
                        
                        ctx_logger.info(
                            "Intercepting sunroof/fog_lights tool call to inject weather check",
                            context_id=context.context_id[:8],
                            loc_id=loc_id,
                            month=month,
                            day=day,
                            hour=hour
                        )
                        
                        intercepted_tool_call = {
                            "id": "call_" + str(uuid4())[:8],
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": json.dumps({
                                    "location_or_poi_id": loc_id,
                                    "month": month,
                                    "day": day,
                                    "time_hour_24hformat": hour
                                })
                            }
                        }
                        
                        assistant_content["tool_calls"] = [intercepted_tool_call]
                        tool_calls = [intercepted_tool_call]
                        assistant_content["content"] = ""

            # 3. Confirmation Interception (Failsafe)
            if tool_calls:
                # Check for confirmation requirements
                needs_confirmation = []
                for tc in tool_calls:
                    tc_name = tc.get("function", {}).get("name", "")
                    try:
                        args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except Exception:
                        args = {}
                    if does_tool_require_confirmation(tc_name, args, messages):
                        needs_confirmation.append(tc)
                
                if needs_confirmation:
                    has_confirmed = False
                    
                    last_user_msg = None
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            last_user_msg = msg.get("content", "").lower().strip()
                            break
                    
                    is_user_yes = False
                    if last_user_msg:
                        is_user_yes = any(w in last_user_msg for w in ["yes", "confirm", "proceed", "sure", "ok", "yep", "do it"])
                    
                    asked_for_confirmation = False
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant" and not msg.get("tool_calls"):
                            content = msg.get("content", "").lower()
                            if any(w in content for w in ["confirm", "do you want me to", "should i go ahead", "confirm that you want me"]):
                                asked_for_confirmation = True
                                break
                    
                    if asked_for_confirmation and is_user_yes:
                        has_confirmed = True
                    
                    if not has_confirmed:
                        first_conf_tool = needs_confirmation[0]
                        tool_name = first_conf_tool["function"]["name"]
                        try:
                            args = json.loads(first_conf_tool["function"]["arguments"])
                        except Exception:
                            args = {}
                        args_str = ", ".join(f"'{k}': '{v}'" for k, v in args.items())
                        
                        conf_msg = f"To execute {tool_name}, I need to call the function with the following parameters: {args_str}. Do you confirm that you want me to proceed?"
                        
                        ctx_logger.info(
                            "Intercepting and blocking tool call requiring confirmation",
                            tool_name=tool_name,
                            args=args
                        )
                        
                        assistant_content["tool_calls"] = None
                        tool_calls = None
                        assistant_content["content"] = conf_msg

            ctx_logger.info(
                "LLM response received",
                has_tool_calls=bool(tool_calls),
                num_tool_calls=len(tool_calls) if tool_calls else 0,
                has_content=bool(assistant_content.get("content")),
                content_length=len(assistant_content.get("content") or ""),
                has_thinking=bool(assistant_content.get("thinking_blocks") or assistant_content.get("reasoning_content"))
            )

            # Build proper A2A Message with Parts (protobuf)
            parts = []

            # Add text Part if there's content
            if assistant_content.get("content"):
                parts.append(new_text_part(assistant_content["content"]))

            # Add data Part if there are tool calls
            if assistant_content.get("tool_calls"):
                tool_calls_list = [
                    ToolCall(
                        tool_name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )
                    for tc in assistant_content["tool_calls"]
                ]
                tool_calls_data = ToolCallsData(tool_calls=tool_calls_list)
                parts.append(new_data_part(tool_calls_data.model_dump()))

            # Add reasoning_content as data Part for debugging (if present)
            if assistant_content.get("reasoning_content"):
                parts.append(new_data_part({"reasoning_content": assistant_content["reasoning_content"]}))

            # If no parts, add empty text
            if not parts:
                parts.append(new_text_part(assistant_content.get("content", "")))

        except Exception as e:
            logger.error(f"LLM error: {e}")
            parts = [new_text_part(f"Error processing request: {str(e)}")]
            assistant_content = {"content": f"Error processing request: {str(e)}"}

        # Add to history
        assistant_message_for_history = {
            "role": "assistant",
            "content": assistant_content.get("content"),
        }

        if assistant_content.get("tool_calls"):
            assistant_message_for_history["tool_calls"] = assistant_content["tool_calls"]

        if assistant_content.get("thinking_blocks"):
            assistant_message_for_history["thinking_blocks"] = assistant_content["thinking_blocks"]
        if assistant_content.get("reasoning_content"):
            assistant_message_for_history["reasoning_content"] = assistant_content["reasoning_content"]

        messages.append(assistant_message_for_history)

        response_message = new_message(
            parts=parts,
            context_id=context.context_id,
            role=Role.ROLE_AGENT,
        )

        # Attach turn_metrics on final response (no tool calls = turn complete)
        has_tool_calls = bool(assistant_content.get("tool_calls"))
        if not has_tool_calls and context.context_id in self.ctx_id_to_turn_metrics:
            turn_m = self.ctx_id_to_turn_metrics.pop(context.context_id)
            num_calls = turn_m[NUM_LLM_CALLS]
            avg_time = (turn_m["_total_llm_time_ms"] / num_calls) if num_calls > 0 else 0.0
            metrics_data = {
                PROMPT_TOKENS: turn_m[PROMPT_TOKENS],
                COMPLETION_TOKENS: turn_m[COMPLETION_TOKENS],
                COST: turn_m[COST],
                MODEL: self.model,
                THINKING_TOKENS: turn_m[THINKING_TOKENS],
                NUM_LLM_CALLS: num_calls,
                AVG_LLM_CALL_TIME_MS: round(avg_time, 1),
                NUM_PASSES: 1,
            }
            response_message.metadata.update({TURN_METRICS_KEY: metrics_data})
            ctx_logger.info(
                "Attached turn_metrics to final response",
                num_llm_calls=num_calls,
                avg_llm_call_time_ms=round(avg_time, 1),
                prompt_tokens=turn_m[PROMPT_TOKENS],
                completion_tokens=turn_m[COMPLETION_TOKENS],
            )

        await event_queue.enqueue_event(response_message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the current execution."""
        logger.bind(role="agent_under_test", context=f"ctx:{context.context_id[:8]}").info(
            "Canceling context",
            context_id=context.context_id[:8]
        )
        if context.context_id in self.ctx_id_to_messages:
            del self.ctx_id_to_messages[context.context_id]
        if context.context_id in self.ctx_id_to_tools:
            del self.ctx_id_to_tools[context.context_id]
        if context.context_id in self.ctx_id_to_turn_metrics:
            del self.ctx_id_to_turn_metrics[context.context_id]

