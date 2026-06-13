"""
DeepFind Engine — System and Control Endpoints
"""
import logging
import os
import threading
import time
from fastapi import APIRouter, Header, Request, HTTPException, status
from pydantic import BaseModel
from utils.resource_monitor import get_system_resources

log = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/resources")
def get_resources():
    """
    Get live system resources including storage sizes, backend RAM, and CPU.
    """
    try:
        return get_system_resources()
    except Exception as e:
        log.error(f"Failed to fetch system resources: {e}")
        return {"status": "error", "error": str(e)}

class ShutdownResponse(BaseModel):
    status: str
    message: str

@router.post("/shutdown", response_model=ShutdownResponse, include_in_schema=False)
def shutdown_server(
    request: Request,
    x_deepfind_control_token: str | None = Header(None)
):
    """
    Authenticated graceful shutdown endpoint.
    Only accessible via loopback interface with the correct control token.
    """
    # 1. Enforce loopback caller
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        log.warning(f"Rejected shutdown request from non-loopback IP: {client_host}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # 2. Verify control token
    expected_token = os.environ.get("DEEPFIND_CONTROL_TOKEN")
    if not expected_token:
        # If no token is configured in the environment, we do not allow shutdown via API.
        log.warning("Shutdown requested but no DEEPFIND_CONTROL_TOKEN is configured in the environment.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if not x_deepfind_control_token or x_deepfind_control_token != expected_token:
        log.warning("Shutdown requested with invalid or missing token.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    log.info("Shutdown endpoint called. Initiating graceful shutdown via Uvicorn server.should_exit.")
    
    def _do_shutdown():
        # Allow the HTTP response to be sent before stopping the server
        time.sleep(1.0)
        import runtime_control
        if runtime_control.server:
            runtime_control.server.should_exit = True
        else:
            log.error("runtime_control.server is not set. Cannot trigger graceful shutdown.")
            
    threading.Thread(target=_do_shutdown, daemon=True).start()
    return ShutdownResponse(status="ok", message="Shutting down gracefully")
