"""
CAR-bench Agent (Cerebras) - Purple agent using Cerebras Inference API.

This is the Track 2 baseline agent. It:
1. Receives task descriptions with available tools from the green agent
2. Decides which tool to call or how to respond
3. Returns responses in the expected JSON format wrapped in A2A protocol

Uses the Cerebras SDK directly for fastest inference with server-side timing.
"""
import json
import os
import time
from pathlib import Path
import sys

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.helpers.proto_helpers import new_message, new_text_part, new_data_part
from a2a.types import Role
from cerebras.cloud.sdk import Cerebras
from google.protobuf.json_format import MessageToDict

sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import configure_logger
from tool_call_types import ToolCall, ToolCallsData
from turn_metrics import (
    TURN_METRICS_KEY, PROMPT_TOKENS, COMPLETION_TOKENS, COST, MODEL,
    THINKING_TOKENS, NUM_LLM_CALLS, AVG_LLM_CALL_TIME_MS, NUM_PASSES,
)
sys.path.pop(0)

logger = configure_logger(role="agent", context="-")

SYSTEM_PROMPT = """You are a helpful car voice assistant. Follow the policy and tool instructions provided."""


class CARBenchAgentExecutor(AgentExecutor):
    """Executor for the CAR-bench purple agent using Cerebras Inference API."""

    def __init__(self, model: str, temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.client = Cerebras()  # Uses CEREBRAS_API_KEY env var
        self.ctx_id_to_messages: dict[str, list[dict]] = {}
        self.ctx_id_to_tools: dict[str, list[dict]] = {}
        self.ctx_id_to_turn_metrics: dict[str, dict] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        inbound_message = context.message
        ctx_logger = logger.bind(role="agent", context=f"ctx:{context.context_id[:8]}")

        # Initialize or get conversation history
        if context.context_id not in self.ctx_id_to_messages:
            self.ctx_id_to_messages[context.context_id] = []

        messages = self.ctx_id_to_messages[context.context_id]
        tools = self.ctx_id_to_tools.get(context.context_id, [])

        # Parse the incoming A2A Message with Parts (protobuf)
        user_message_text = None
        incoming_tool_results = None

        try:
            for part in inbound_message.parts:
                content_type = part.WhichOneof("content")
                if content_type == "text":
                    text = part.text
                    if "System:" in text and "\n\nUser:" in text:
                        parts_split = text.split("\n\nUser:", 1)
                        system_prompt = parts_split[0].replace("System:", "").strip()
                        user_message_text = parts_split[1].strip()
                        if not messages:
                            messages.append({"role": "system", "content": system_prompt})
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

            ctx_logger.info(
                "Received user message",
                context_id=context.context_id[:8],
                turn=len(messages) + 1,
                message_preview=(user_message_text[:100] if user_message_text else
                                 f"[{len(incoming_tool_results)} tool results]" if incoming_tool_results else "")
            )

        except Exception as e:
            logger.warning(f"Failed to parse message parts: {e}, using fallback")
            user_message_text = context.get_user_input()

        # Format tool results if previous message had tool calls
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
                        })
                    else:
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_call_id", tr.get("toolCallId", f"unknown_{tr_name}")),
                            "content": tr.get("content", ""),
                        })
            else:
                tool_results = []
                for tc in prev_tool_calls:
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": user_message_text or "",
                    })

            messages.extend(tool_results)
        else:
            messages.append({"role": "user", "content": user_message_text})

        # Call Cerebras API with retry for rate limits
        try:
            # Build request kwargs
            request_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
            if tools:
                request_kwargs["tools"] = tools

            call_start_time = time.perf_counter()

            # Retry loop for 429 rate limit errors
            max_retries = 2
            retry_delay = 2.0
            response = None
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(**request_kwargs)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        ctx_logger.warning(
                            "Rate limited, retrying",
                            attempt=attempt + 1,
                            retry_delay=retry_delay,
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise

            call_elapsed_ms = (time.perf_counter() - call_start_time) * 1000.0

            # Use server-side timing if available (more accurate)
            if hasattr(response, "time_info") and response.time_info:
                # completion_time = actual inference time on Cerebras hardware
                server_time_ms = response.time_info.completion_time * 1000.0
                if server_time_ms > 0:
                    call_elapsed_ms = server_time_ms

            # Accumulate turn metrics
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
            usage = response.usage
            if usage:
                turn_m[PROMPT_TOKENS] += usage.prompt_tokens or 0
                turn_m[COMPLETION_TOKENS] += usage.completion_tokens or 0
                if hasattr(usage, "completion_tokens_details") and usage.completion_tokens_details:
                    turn_m[THINKING_TOKENS] += getattr(usage.completion_tokens_details, "reasoning_tokens", 0) or 0
            turn_m[NUM_LLM_CALLS] += 1
            turn_m["_total_llm_time_ms"] += call_elapsed_ms

            # Parse the response
            llm_message = response.choices[0].message
            content = llm_message.content
            tool_calls = llm_message.tool_calls
            reasoning = getattr(llm_message, "reasoning", None)

            ctx_logger.info(
                "LLM response received",
                has_tool_calls=bool(tool_calls),
                num_tool_calls=len(tool_calls) if tool_calls else 0,
                has_content=bool(content),
                inference_ms=round(call_elapsed_ms, 1),
            )
            ctx_logger.debug(
                "LLM response details",
                context_id=context.context_id[:8],
                content=content,
                tool_calls=[{"name": tc.function.name, "args": tc.function.arguments} for tc in tool_calls] if tool_calls else None,
                has_reasoning=bool(reasoning),
            )

            # Build A2A response Parts
            parts = []

            if content:
                parts.append(new_text_part(content))

            if tool_calls:
                tool_calls_list = [
                    ToolCall(
                        tool_name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                    for tc in tool_calls
                ]
                tool_calls_data = ToolCallsData(tool_calls=tool_calls_list)
                parts.append(new_data_part(tool_calls_data.model_dump()))

            if reasoning:
                parts.append(new_data_part({"reasoning_content": reasoning}))

            if not parts:
                parts.append(new_text_part(content or ""))

        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            parts = [new_text_part(f"Error processing request: {str(e)}")]
            content = f"Error processing request: {str(e)}"
            tool_calls = None

        # Add to conversation history
        assistant_message_for_history = {
            "role": "assistant",
            "content": content,
        }
        if tool_calls:
            assistant_message_for_history["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]
        messages.append(assistant_message_for_history)

        # Build response message
        response_message = new_message(
            parts=parts,
            context_id=context.context_id,
            role=Role.ROLE_AGENT,
        )

        # Attach turn_metrics on final response (no tool calls = turn complete)
        has_tool_calls = bool(tool_calls)
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
        logger.bind(role="agent", context=f"ctx:{context.context_id[:8]}").info(
            "Canceling context",
            context_id=context.context_id[:8]
        )
        if context.context_id in self.ctx_id_to_messages:
            del self.ctx_id_to_messages[context.context_id]
        if context.context_id in self.ctx_id_to_tools:
            del self.ctx_id_to_tools[context.context_id]
        if context.context_id in self.ctx_id_to_turn_metrics:
            del self.ctx_id_to_turn_metrics[context.context_id]
