import asyncio
import aiosqlite
import logging
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException
from typing import List
from socketManager import manager


logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app=FastAPI()

DB_PATH = 'database.db'
db_connection = None

@app.on_event("startup")
async def startup():
    global db_connection
    db_connection = await aiosqlite.connect(DB_PATH)
    await db_connection.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL
        )
    ''')
    await db_connection.commit()
    logger.info("Database connection created")

@app.on_event("shutdown")
async def shutdown():
    global db_connection
    if db_connection:
        await db_connection.close()
    logger.info("Database connection closed")

async def enroll_student_db(student_id:int,course_id:int):
    try:
        await db_connection.execute(
            "INSERT INTO enrollments (student_id,course_id) VALUES(?,?)", (student_id,course_id)
        )
        await db_connection.commit()
        return True
    except Exception as e:
        logger.info(f"database error occured {e}")
        return False
@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data=await websocket.receive_text()
            await websocket.send_text(f"Echo:{data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/enroll/{student_id}/{course_id}")
async def enroll(student_id:int,course_id:int):
    logger.info(f"Attempting to enroll Student {student_id} in Course {course_id}")
    success=await enroll_student_db(student_id,course_id)
    if not success:
        raise HTTPException(status_code=500 , detail="enrollments failed")
    message=f"Student {student_id} enrolled in {course_id}"
    await manager.broadcast(message)
    return {"message":"Student enrolled successfully"}
        



