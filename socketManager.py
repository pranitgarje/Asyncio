from fastapi import WebSocket
from typing import List
import logging

logger = logging.getLogger(__name__)

class SocketManager:
    def __init__(self):
        self.active_connections:List[WebSocket]=[]
    
    async def connect(self,websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("new connection added")
    
    def disconnect(self,websocket:WebSocket):
        self.active_connections.remove(websocket)
        logger.info("web socket client closed")
    
    async def broadcast(self,message:str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager=SocketManager()  