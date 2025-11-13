"""
WebSocket for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
from loguru import logger
import json
import asyncio
from backend.constants import WEBSOCKET_MAX_CONNECTIONS


class ConnectionManager:
    """Thread-safe WebSocket connection manager using asyncio locks"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        logger.info("ConnectionManager initialized with thread-safe operations")

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection (thread-safe)"""
        try:
            await websocket.accept()
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {type(e).__name__}: {e}")
            return

        async with self._lock:
            # Check connection limit
            if len(self.active_connections) >= WEBSOCKET_MAX_CONNECTIONS:
                logger.warning(f"Max WebSocket connections ({WEBSOCKET_MAX_CONNECTIONS}) reached, rejecting new connection")
                try:
                    await websocket.close(code=1008, reason="Server at max capacity")
                except Exception as e:
                    logger.debug(f"Error closing WebSocket: {e}")
                return

            self.active_connections.append(websocket)
            logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection (thread-safe)"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection with error handling"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.debug(f"Error sending personal message: {type(e).__name__}: {e}")
            # Disconnect the websocket if send fails
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict):
        """Broadcast message to all connections (thread-safe)"""
        async with self._lock:
            if not self.active_connections:
                return  # No connections to broadcast to

            message_text = json.dumps(message)
            disconnected = []

            # Make a copy to iterate safely
            connections_copy = list(self.active_connections)

        # Send messages outside the lock to avoid blocking other operations
        for connection in connections_copy:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.debug(f"Error broadcasting to connection: {type(e).__name__}: {e}")
                disconnected.append(connection)

        # Remove disconnected connections (acquire lock again)
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)
    
    def broadcast_sync(self, message: Dict):
        """Synchronous broadcast wrapper (creates task if needed)"""
        try:
            # Try to get the running event loop
            loop = asyncio.get_running_loop()
            # Already in async context, create task
            asyncio.create_task(self.broadcast(message))
            logger.debug("WebSocket broadcast queued as async task")
        except RuntimeError:
            # No running loop - try to get existing event loop
            try:
                loop = asyncio.get_event_loop()
                if loop and loop.is_running():
                    asyncio.create_task(self.broadcast(message))
                    logger.debug("WebSocket broadcast created as task on existing loop")
                else:
                    logger.debug("Skipping WebSocket broadcast - no running event loop")
            except RuntimeError as e:
                # No event loop at all
                logger.debug(f"Skipping WebSocket broadcast - no event loop available: {e}")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates with proper error handling
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle different message types
                if message_type == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Subscribe to updates (e.g., for agent progress)
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "message": "Subscribed to updates"
                        }),
                        websocket
                    )
                else:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }),
                        websocket
                    )

            except json.JSONDecodeError as e:
                logger.debug(f"Invalid JSON received: {type(e).__name__}")
                try:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }),
                        websocket
                    )
                except Exception as send_error:
                    logger.debug(f"Error sending error message: {type(send_error).__name__}")
                    break

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.debug("WebSocket client disconnected gracefully")
    except Exception as e:
        logger.error(f"WebSocket error: {type(e).__name__}: {e}")
        await manager.disconnect(websocket)


def broadcast_agent_progress(agent_name: str, step: str, data: Dict):
    """Broadcast agent progress update (thread-safe)"""
    from datetime import datetime
    message = {
        "type": "agent_progress",
        "agent": agent_name,
        "step": step,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    try:
        manager.broadcast_sync(message)
    except Exception as e:
        logger.debug(f"Failed to broadcast agent progress: {type(e).__name__}: {e}")


def broadcast_search_results(query: str, results_count: int):
    """Broadcast search results (thread-safe)"""
    from datetime import datetime
    message = {
        "type": "search_complete",
        "query": query,
        "results_count": results_count,
        "timestamp": datetime.now().isoformat()
    }
    try:
        manager.broadcast_sync(message)
    except Exception as e:
        logger.debug(f"Failed to broadcast search results: {type(e).__name__}: {e}")
