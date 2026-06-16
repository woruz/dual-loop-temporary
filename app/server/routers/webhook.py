import hashlib
import hmac
import logging
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from app.core.use_cases.process_webhook import ProcessWebhookUseCase
from app.server.dependencies import get_process_webhook_use_case, get_token_generator

logger = logging.getLogger("app.server.routers.webhook")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")
        

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting message to {len(self.active_connections)} active WebSocket connections.")
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send JSON to a WebSocket connection: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Manually check authorization token from cookies or query params
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    if not token:
        logger.warning("WebSocket handshake failed: Access token missing in cookies and query parameters.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify the token
    token_generator = get_token_generator()
    payload = token_generator.verify_token(token)
    if not payload or not payload.get("sub"):
        logger.warning("WebSocket handshake failed: Invalid or expired access token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept the connection
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but must read to detect disconnections
            data = await websocket.receive_text()
            logger.debug(f"Received unexpected message from WebSocket client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket session: {e}", exc_info=True)
        manager.disconnect(websocket)

def get_webhook_secret() -> Optional[str]:
    """Retrieves GITHUB_WEBHOOK_SECRET environment variable."""
    return os.getenv("GITHUB_WEBHOOK_SECRET")


async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)) -> None:
    """
    Dependency function to verify the HMAC signature of incoming GitHub Webhooks.
    Skips validation if GITHUB_WEBHOOK_SECRET is not configured.
    """
    secret = get_webhook_secret()
    if not secret:
        logger.warning(
            "SECURITY WARNING: GITHUB_WEBHOOK_SECRET environment variable is not set. "
            "Skipping signature validation. DO NOT USE IN PRODUCTION."
        )
        return

    if not x_hub_signature_256:
        logger.error("Signature Validation Failed: Missing X-Hub-Signature-256 header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing GitHub signature header (X-Hub-Signature-256)",
        )

    try:
        body_bytes = await request.body()
    except Exception as e:
        logger.exception("Failed to read raw request body for signature verification.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read request body"
        )

    # Calculate expected signature
    hmac_obj = hmac.new(
        key=secret.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256
    )
    expected_signature = f"sha256={hmac_obj.hexdigest()}"

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.error("Signature Validation Failed: HMAC SHA-256 signature mismatch.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature. Validation failed.",
        )
    logger.info("GitHub webhook signature successfully verified.")


@router.post("/github")
async def github_webhook_receiver(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    _signature_verification: None = Depends(verify_signature),
    use_case: ProcessWebhookUseCase = Depends(get_process_webhook_use_case)
) -> Dict[str, Any]:
    """
    Receiver endpoint for GitHub Webhook events.
    Supports 'ping' (for handshake) and 'push' events.
    """
    logger.info(f"Received webhook request. Event: '{x_github_event}'")

    if not x_github_event:
        logger.error("Webhook processing aborted: Missing X-GitHub-Event header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-GitHub-Event header",
        )

    if x_github_event == "ping":
        logger.info("GitHub Webhook handshake successful: Received ping event.")
        return {
            "status": "success",
            "message": "Connection established successfully. Webhook receiver is listening."
        }

    if x_github_event == "push":
        try:
            payload = await request.json()
        except Exception as e:
            logger.exception("Failed to parse incoming request body as JSON.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body must be a valid JSON payload",
            )

        try:
            result = await use_case.execute(payload)
            
            # Broadcast the push event details to active WebSocket clients
            try:
                repo_name = payload.get("repository", {}).get("full_name", "")
                ref = payload.get("ref", "")
                branch = ref.split("/")[-1] if ref else "unknown_branch"
                
                # Retrieve sender username or fallback
                sender_username = payload.get("sender", {}).get("login")
                if not sender_username:
                    incoming_commits = payload.get("commits", [])
                    if incoming_commits:
                        author_data = incoming_commits[0].get("author", {})
                        sender_username = author_data.get("username") or author_data.get("name") or "unknown"
                    else:
                        sender_username = "unknown"

                commits_list = []
                for item in payload.get("commits", []):
                    commits_list.append({
                        "author": item.get("author", {}).get("username") or item.get("author", {}).get("name") or sender_username,
                        "commit_sha": item.get("id") or item.get("commit_sha") or "unknown_sha",
                        "commit_message": item.get("message") or "No message"
                    })
                
                websocket_message = {
                    "repository": repo_name,
                    "branch": branch,
                    "message": result.get("message", f"Successfully processed {len(commits_list)} commits."),
                    "payload": {
                        "commits": commits_list
                    }
                }
                await manager.broadcast(websocket_message)
            except Exception as broadcast_err:
                logger.error(f"Failed to broadcast webhook event over WebSocket: {broadcast_err}", exc_info=True)

            return result
        except ValueError as val_err:
            logger.warning(f"Webhook execution failure (bad input): {val_err}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(val_err)
            )
        except Exception as e:
            logger.exception("Unexpected error occurred while processing webhook payload.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during webhook processing"
            )

    logger.info(f"Ignored webhook event: Event type '{x_github_event}' is currently unhandled.")
    return {
        "status": "ignored",
        "message": f"Webhook event '{x_github_event}' is currently unhandled."
    }






