import argparse
import asyncio
import sys
import uvicorn
from pathlib import Path
import importlib
import logging

# Configure basic logging – the parent runners (run_backend_only / run_full_system) will stream stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional WebSocket server integration
# ---------------------------------------------------------------------------
async def _start_websocket_server(host: str, port: int):
    """Start the built-in WebSocket server if it's available."""
    try:
        from backend.services.websocket_server import WebSocketServer  # noqa: WPS433 (dynamic import ok here)
    except ImportError:
        try:
            # Fallback if script executed from inside backend directory
            from services.websocket_server import WebSocketServer  # type: ignore
        except ImportError:
            logger.warning("WebSocketServer implementation not found – skipping WebSocket startup")
            return

    ws_server = WebSocketServer(host=host, port=port)
    logger.info("Starting internal WebSocket server on ws://%s:%s", host, port)
    await ws_server.start_server()


def main() -> None:  # noqa: WPS231 (centralized entrypoint)
    parser = argparse.ArgumentParser(description="Launch FastAPI backend and optional WebSocket server")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server (default: 8000)")
    parser.add_argument("--ws-port", type=int, default=8765, help="Port for WebSocket server (default: 8765)")
    parser.add_argument("--no-ws", action="store_true", help="Disable WebSocket server startup")
    args = parser.parse_args()

    # Ensure project root is on sys.path so `backend` resolves when executed from root
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # ---------------------------------------------------------------------
    # Launch FastAPI backend via uvicorn
    # ---------------------------------------------------------------------
    config = uvicorn.Config("backend.main:app", host=args.host, port=args.port, log_level="info", reload=False)
    server = uvicorn.Server(config)

    # Decide whether to run websocket server
    if args.no_ws:
        logger.info("WebSocket startup skipped via --no-ws flag")
        # Blocking call – run forever
        server.run()
        return

    async def _run():
        ws_task = None
        try:
            if not args.no_ws:
                ws_task = asyncio.create_task(_start_websocket_server(args.host, args.ws_port))

            # Run uvicorn within the same event loop
            await server.serve()
        finally:
            if ws_task:
                ws_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await ws_task

    import contextlib
    asyncio.run(_run())


if __name__ == "__main__":
    main()