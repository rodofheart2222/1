#!/usr/bin/env python3
"""
Unified Startup Script

Starts the backend API (FastAPI/uvicorn) and WebSocket server, optionally the frontend dev server,
runs backend tests once, and then keeps services running until interrupted.

Usage examples:
  - python startup.py
  - python startup.py --no-frontend
  - python startup.py --host 0.0.0.0 --api-port 8000 --ws-port 8765 --frontend-port 3000
  - python startup.py --no-tests  # skip running pytest
  - python startup.py --exit-on-test-fail  # stop services if tests fail

Notes:
  - Uses `backend/config/environment.py` when available for defaults.
  - Waits for the backend health endpoint before running tests.
  - Frontend start is optional (off by default in many headless/dev containers).
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional


def ensure_pythonpath() -> None:
	"""Ensure project root and backend are on PYTHONPATH for subprocesses."""
	root = Path(__file__).parent.resolve()
	backend = root / "backend"
	paths = [str(root), str(backend)]
	pythonpath = os.environ.get("PYTHONPATH", "")
	for p in paths:
		if p not in sys.path:
			sys.path.insert(0, p)
		if p not in pythonpath:
			pythonpath = f"{p}{os.pathsep}{pythonpath}" if pythonpath else p
	os.environ["PYTHONPATH"] = pythonpath


def get_config_defaults() -> Dict[str, object]:
	"""Read default config from backend/config/environment.py if available."""
	ensure_pythonpath()
	try:
		from backend.config.environment import Config
		return {
			"host": Config.get_host(),
			"api_port": Config.get_api_port(),
			"ws_port": Config.get_ws_port(),
			"frontend_port": Config.get_frontend_port(),
			"auth_token": Config.get_auth_token(),
			"external_host": Config.get_external_host(),
			"environment": "production" if Config.is_production() else "development",
		}
	except Exception:
		return {
			"host": "0.0.0.0",
			"api_port": 8000,
			"ws_port": 8765,
			"frontend_port": 3000,
			"auth_token": "dashboard_token_2024",
			"external_host": "127.0.0.1",
			"environment": "development",
		}


class ProcessHandle:
	def __init__(self, name: str, popen: subprocess.Popen):
		self.name = name
		self.popen = popen
		self._thread: Optional[threading.Thread] = None

	def attach_logger(self) -> None:
		def _reader():
			try:
				for line in iter(self.popen.stdout.readline, ''):
					if not line:
						break
					text = line.rstrip()
					if text:
						print(f"[{self.name}] {text}")
			except Exception as e:
				print(f"[STARTUP] Error reading {self.name} output: {e}")
		self._thread = threading.Thread(target=_reader, daemon=True)
		self._thread.start()

	def terminate(self, timeout: float = 8.0) -> None:
		if self.popen and self.popen.poll() is None:
			try:
				self.popen.terminate()
				self.popen.wait(timeout=timeout)
			except subprocess.TimeoutExpired:
				self.popen.kill()
				self.popen.wait()
			except Exception as e:
				print(f"[STARTUP] Error terminating {self.name}: {e}")


class StartupOrchestrator:
	def __init__(self, host: str, api_port: int, ws_port: int, frontend_port: int,
				 run_tests: bool, start_frontend: bool, exit_on_test_fail: bool,
				 integrated_ws: bool, auth_token: str, external_host: str, environment: str):
		self.host = host
		self.api_port = api_port
		self.ws_port = ws_port
		self.frontend_port = frontend_port
		self.run_tests = run_tests
		self.start_frontend = start_frontend
		self.exit_on_test_fail = exit_on_test_fail
		self.integrated_ws = integrated_ws
		self.auth_token = auth_token
		self.external_host = external_host or ("127.0.0.1" if host == "0.0.0.0" else host)
		self.environment = environment

		self._processes: Dict[str, ProcessHandle] = {}
		self._stop_event = threading.Event()

	def _env_with_paths(self) -> Dict[str, str]:
		env = os.environ.copy()
		env.setdefault("HOST", self.host)
		env.setdefault("PORT", str(self.api_port))
		env.setdefault("WS_PORT", str(self.ws_port))
		env.setdefault("ENVIRONMENT", self.environment or "development")
		# Ensure PYTHONPATH propagated
		env["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")
		return env

	def start_backend(self) -> None:
		cmd = [
			sys.executable, "-m", "uvicorn", "backend.main:app",
			"--host", self.host,
			"--port", str(self.api_port),
			"--log-level", "info",
		]
		print(f"[STARTUP] Launching Backend API: {' '.join(cmd)}")
		proc = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
			bufsize=1,
			env=self._env_with_paths(),
			cwd=str(Path(__file__).parent.resolve()),
		)
		h = ProcessHandle("BACKEND", proc)
		h.attach_logger()
		self._processes["backend"] = h

	def start_websocket(self) -> None:
		# Use the standalone websocket server module to avoid importing optional integration
		cmd = [
			sys.executable, "-m", "backend.services.websocket_server",
			"--host", self.host,
			"--port", str(self.ws_port),
			"--auth-token", self.auth_token,
		]
		print(f"[STARTUP] Launching WebSocket: {' '.join(cmd)}")
		proc = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
			bufsize=1,
			env=self._env_with_paths(),
			cwd=str(Path(__file__).parent.resolve()),
		)
		h = ProcessHandle("WEBSOCKET", proc)
		h.attach_logger()
		self._processes["websocket"] = h

	def start_frontend_server(self) -> None:
		frontend_dir = Path(__file__).parent / "frontend"
		if not frontend_dir.exists() or not (frontend_dir / "package.json").exists():
			print("[STARTUP] Frontend not found; skipping.")
			return
		# Check for npm
		try:
			subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		except Exception:
			print("[STARTUP] npm not available; skipping frontend.")
			return
		env = os.environ.copy()
		env.update({
			"PORT": str(self.frontend_port),
			"HOST": self.external_host,
			"REACT_APP_API_URL": f"http://{self.external_host}:{self.api_port}",
			"REACT_APP_WS_URL": f"ws://{self.external_host}:{self.ws_port}",
			"BROWSER": "none",
		})
		cmd = ["npm", "run", "dev"]
		print(f"[STARTUP] Launching Frontend: cd {frontend_dir} && {' '.join(cmd)}")
		proc = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
			bufsize=1,
			cwd=str(frontend_dir),
			env=env,
		)
		h = ProcessHandle("FRONTEND", proc)
		h.attach_logger()
		self._processes["frontend"] = h

	def wait_for_backend(self, timeout_seconds: int = 60) -> bool:
		print(f"[STARTUP] Waiting for backend health at http://{self.external_host}:{self.api_port}/health ...")
		import urllib.request
		import urllib.error
		start = time.time()
		while time.time() - start < timeout_seconds:
			try:
				with urllib.request.urlopen(f"http://{self.external_host}:{self.api_port}/health", timeout=3) as resp:
					if resp.status == 200:
						print("[STARTUP] Backend is healthy.")
						return True
			except Exception:
				pass
			time.sleep(1)
		print("[STARTUP] Backend did not become healthy in time (continuing anyway).")
		return False

	def run_pytests(self) -> int:
		print("[STARTUP] Running backend tests (pytest)...")
		backend_dir = Path(__file__).parent / "backend"
		cmd = [sys.executable, "-m", "pytest"]
		proc = subprocess.Popen(
			cmd,
			cwd=str(backend_dir),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)
		# Stream output
		try:
			for line in iter(proc.stdout.readline, ''):
				if not line:
					break
				print(f"[TESTS] {line.rstrip()}")
		finally:
			proc.wait()
		code = proc.returncode
		# Pytest exit code 5 means no tests collected; treat as success for startup purposes
		if code == 0:
			print("[STARTUP] Tests passed.")
		elif code == 5:
			print("[STARTUP] No tests collected.")
		else:
			print(f"[STARTUP] Tests failed with exit code {code}.")
		return code

	def stop_all(self) -> None:
		print("[STARTUP] Stopping all services...")
		# Stop in reverse order
		for key in list(self._processes.keys())[::-1]:
			try:
				self._processes[key].terminate()
			except Exception:
				pass
		print("[STARTUP] All services stopped.")

	def run(self) -> int:
		print("=" * 80)
		print("MT5 Dashboard - Unified Startup")
		print("=" * 80)
		print(f"API:        http://{self.external_host}:{self.api_port}")
		print(f"Docs:       http://{self.external_host}:{self.api_port}/docs")
		print(f"Health:     http://{self.external_host}:{self.api_port}/health")
		print(f"WebSocket:  ws://{self.external_host}:{self.ws_port}")
		if self.start_frontend:
			print(f"Frontend:   http://{self.external_host}:{self.frontend_port}")
		print("-" * 80)

		# Start services
		self.start_backend()
		self.wait_for_backend(timeout_seconds=60)
		self.start_websocket()
		if self.start_frontend:
			self.start_frontend_server()

		# Optionally run tests
		if self.run_tests:
			code = self.run_pytests()
			if code not in (0, 5) and self.exit_on_test_fail:
				self.stop_all()
				return code

		print("[STARTUP] Services are running. Press Ctrl+C to stop.")
		# Wait until interrupted
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			print("\n[STARTUP] Interrupt received.")
		finally:
			self.stop_all()
		return 0


def parse_args() -> argparse.Namespace:
	defaults = get_config_defaults()
	parser = argparse.ArgumentParser(description="Start backend, websocket, optional frontend, run tests, and keep running.")
	parser.add_argument("--host", default=defaults["host"], help="Bind host for servers (default from config)")
	parser.add_argument("--api-port", type=int, default=defaults["api_port"], help="Backend API port")
	parser.add_argument("--ws-port", type=int, default=defaults["ws_port"], help="WebSocket port")
	parser.add_argument("--frontend-port", type=int, default=defaults["frontend_port"], help="Frontend dev server port")
	parser.add_argument("--frontend", dest="frontend", action="store_true", help="Start frontend dev server as well")
	parser.add_argument("--no-frontend", dest="frontend", action="store_false", help="Do not start frontend dev server")
	parser.set_defaults(frontend=False)
	parser.add_argument("--run-tests", dest="run_tests", action="store_true", help="Run backend tests with pytest")
	parser.add_argument("--no-tests", dest="run_tests", action="store_false", help="Skip running backend tests")
	parser.set_defaults(run_tests=True)
	parser.add_argument("--exit-on-test-fail", action="store_true", help="Stop services if tests fail")
	parser.add_argument("--integrated-ws", dest="integrated_ws", action="store_true", help="Start websocket with integration services (requires integration module)")
	parser.add_argument("--no-integrated-ws", dest="integrated_ws", action="store_false", help="Start websocket without integration services")
	parser.set_defaults(integrated_ws=False)
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	defaults = get_config_defaults()
	orchestrator = StartupOrchestrator(
		host=args.host,
		api_port=args.api_port,
		ws_port=args.ws_port,
		frontend_port=args.frontend_port,
		run_tests=args.run_tests,
		start_frontend=args.frontend,
		exit_on_test_fail=args.exit_on_test_fail,
		integrated_ws=args.integrated_ws,
		auth_token=defaults.get("auth_token", "dashboard_token_2024"),
		external_host=defaults.get("external_host", "127.0.0.1"),
		environment=defaults.get("environment", "development"),
	)
	# Setup signal handlers for graceful shutdown
	def _handle_signal(signum, frame):
		print(f"\n[STARTUP] Received signal {signum}.")
		orchestrator.stop_all()
		sys.exit(0)
	for s in (signal.SIGINT, signal.SIGTERM):
		try:
			signal.signal(s, _handle_signal)
		except Exception:
			pass
	return orchestrator.run()


if __name__ == "__main__":
	sys.exit(main())