import asyncio
import aiopg
import logging
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException
from typing import List
from socketManager import manager


logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app=FastAPI()

DSN = 'dbname=postgres user=postgres password=password host=127.0.0.1'
db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool=await aiopg.create_pool(DSN)
    logger.info("Database connection pool created")

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
    logger.info("Database connection pool closed")

async def enroll_student_db(student_id:int,course_id:int):
    try:
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO enrollments (student_id,course_id) VALUES(%s,%s)" , (student_id,course_id)
                )
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
