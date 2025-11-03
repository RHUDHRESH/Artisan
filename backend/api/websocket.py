"""
WebSocket for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from loguru import logger
import json


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connections"""
        if not self.active_connections:
            return  # No connections to broadcast to
            
        message_text = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.debug(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    def broadcast_sync(self, message: Dict):
        """Synchronous broadcast wrapper (creates task if needed)"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Already in async context, create task
            asyncio.create_task(self.broadcast(message))
        except RuntimeError:
            # No running loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.broadcast(message))
                else:
                    loop.run_until_complete(self.broadcast(message))
            except RuntimeError:
                # No event loop at all, skip broadcast to avoid asyncio.run() error
                logger.debug(f"Skipping WebSocket broadcast - no event loop available")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
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
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


def broadcast_agent_progress(agent_name: str, step: str, data: Dict):
    """Broadcast agent progress update"""
    manager.broadcast({
        "type": "agent_progress",
        "agent": agent_name,
        "step": step,
        "data": data,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    })


def broadcast_search_results(query: str, results_count: int):
    """Broadcast search results"""
    manager.broadcast({
        "type": "search_complete",
        "query": query,
        "results_count": results_count,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    })
