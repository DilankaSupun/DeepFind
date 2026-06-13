"""
DeepFind Engine — Runtime Control
Holds the Uvicorn server instance and handles graceful shutdown coordination.
"""
import threading

server = None
shutdown_event = threading.Event()
