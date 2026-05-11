"""Server entry point for CAR-bench purple agent (Cerebras)."""
import argparse
import os
import sys
from pathlib import Path

import uvicorn
from starlette.applications import Starlette

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.routes import create_jsonrpc_routes, create_agent_card_routes
from a2a.types import AgentCard

from car_bench_agent import CARBenchAgentExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_utils import configure_logger
sys.path.pop(0)

logger = configure_logger(role="agent", context="server")


def prepare_agent_card(url: str) -> AgentCard:
    """Create the agent card for the CAR-bench purple agent (Cerebras)."""
    card = AgentCard(
        name="car_bench_agent_cerebras",
        description="In-car voice assistant agent for CAR-bench (Cerebras Track 2)",
        version="1.0.0",
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
    )

    iface = card.supported_interfaces.add()
    iface.url = url
    iface.protocol_binding = "JSONRPC"
    iface.protocol_version = "1.0"

    card.capabilities.streaming = False
    card.capabilities.push_notifications = False
    card.capabilities.extended_agent_card = False

    skill = card.skills.add()
    skill.id = "car_assistant"
    skill.name = "In-Car Voice Assistant (Cerebras)"
    skill.description = "Helps drivers with navigation, communication, charging, and other in-car tasks using Cerebras inference"
    skill.tags.extend(["benchmark", "car-bench", "voice-assistant", "cerebras", "track2"])

    return card


def main():
    parser = argparse.ArgumentParser(description="Run the CAR-bench agent (Cerebras Track 2).")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="External URL for the agent card")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Cerebras model (can also be set via CEREBRAS_MODEL env var)"
    )
    parser.add_argument("--temperature", type=float, default=0.0, help="Temperature for the LLM")
    args = parser.parse_args()

    model = args.model or os.getenv("CEREBRAS_MODEL", "qwen-3-235b-a22b-instruct-2507")
    temperature = args.temperature or float(os.getenv("CEREBRAS_TEMPERATURE", "0.0"))

    logger.info(
        "Starting CAR-bench agent (Cerebras)",
        model=model,
        temperature=temperature,
        host=args.host,
        port=args.port,
    )

    card = prepare_agent_card(args.card_url or f"http://{args.host}:{args.port}/")

    request_handler = DefaultRequestHandler(
        agent_executor=CARBenchAgentExecutor(
            model=model,
            temperature=temperature,
        ),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )

    routes = create_jsonrpc_routes(request_handler, "/", enable_v0_3_compat=True)
    card_routes = create_agent_card_routes(card)

    app = Starlette(routes=routes + card_routes)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        timeout_keep_alive=1000,
    )


if __name__ == "__main__":
    main()
