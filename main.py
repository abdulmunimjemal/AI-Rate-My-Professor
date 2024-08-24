# Updated WebSocket App Code

import asyncio
import time
import os
from dotenv import load_dotenv
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from agent import ProfessorRaterAgent
from langchain_core.messages import HumanMessage, AIMessage
from tools.ratemyprofessor import run_tools

load_dotenv()

# CONSTANTS
SECRET_KEY = os.getenv("SECRET_KEY", "S@MPL3")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 60))
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "1024"))
STREAM = True # os.getenv("STREAM", "False").lower() == "true"

# App Setup
app = FastAPI(
    title="Rate My Professor",
    description="A chatbot that helps you find professors based on your requirements using AI and Rate My Professor DB.",
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")
agent = ProfessorRaterAgent()

# In Memory Storage (Will later be replaced with Redis)
user_sessions: Dict[str, WebSocket] = {}  # Active sessions
chat_history: Dict[str, List[str]] = {}  # Chat history for each session
session_timestamps: Dict[str, float] = {}  # Last active time for each session

@app.get("/")
async def get(request: Request):
    """
    Serve the chat interface and manage session state.
    """
    ws_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/chat")
     
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in session_timestamps:
        if time.time() - session_timestamps[session_id] > SESSION_TIMEOUT:
            # Clear expired session
            del chat_history[session_id]
            del session_timestamps[session_id]
            session_id = None
    elif session_id and session_id not in session_timestamps:
        session_id = None

    if not session_id:
        session_id = str(uuid4())
    
    # Update session timestamps and chat history
    session_timestamps[session_id] = time.time()
    chat_history[session_id] = []

    response = templates.TemplateResponse("chat.html", {"request": request, "ws_url": ws_url})
    response.set_cookie("session_id", session_id)
    return response

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling real-time chat messages.
    """
    await websocket.accept()

    session_id = websocket.cookies.get("session_id")
    if not session_id:
        await websocket.close()
        return
    
    if not session_id in chat_history: # Create new session if not found
        chat_history[session_id] = []
        session_timestamps[session_id] = time.time()
        
    try:
        while True:
            human_message = await websocket.receive_text()
            ai_message = []
            if STREAM:
                await websocket.send_text("<STREAM>")
                buffer = ""
                for chunk in agent.invoke(human_message, chat_history[session_id]):                   
                    buffer += chunk  # Add chunk to buffer
                    if "NO PROFESSOR" in buffer:
                        buffer = "I could not find anything relavant in my database.\
                            I will try to make tool call to help you. Please wait for a moment."
                        await websocket.send_text(buffer)
                        await websocket.send_text("<END>")  # Send end of stream
                        
                        ai_response = run_tools(human_message, chat_history=chat_history[session_id]) # Call the tool
                        await websocket.send_text("<STREAM>")  # Start new stream
                        await websocket.send_text(ai_response)
                        await websocket.send_text("<END>")  # Send end of stream
                        ai_message.append(ai_response)
                        buffer = ""
                        break
                    
                    elif len(buffer) >= BUFFER_SIZE:  # Check if buffer size is exceeded                  
                        await websocket.send_text(buffer)  # Send buffered data
                        buffer = ""  # Clear the buffer
                    
                        ai_message.append(chunk)
                    # await asyncio.sleep(0.01)
                
                # Send any remaining data in the buffer
                if buffer:
                    await websocket.send_text(buffer)
                
                await websocket.send_text("<END>")
                ai_message = "".join(ai_message)
            else: # No Streaming
                ai_message = agent.invoke(human_message, chat_history[session_id])
                if "NO PROFESSOR" in ai_message:
                    buffer = "I could not find anything relavant in my databse.\
                            I will try to make tool call to help you. Please wait for a moment."
                    await websocket.send_text(buffer)
                    ai_response = run_tools(human_message, chat_history=chat_history) # Call the toolnd(ai_response)
                await websocket.send_text(ai_message)

            chat_history[session_id].append(HumanMessage(human_message))
            chat_history[session_id].append(AIMessage(ai_message))
            session_timestamps[session_id] = time.time()

    except WebSocketDisconnect:
        # Log disconnection and remove session
        if session_id in user_sessions:
            del user_sessions[session_id]
        print(f"WebSocket disconnected for session {session_id}.")
    # except Exception as e:
        
    #     print(f"Error occurred for session {session_id}: {str(e)}")
        # await websocket.close()

async def session_cleanup_task():
    """
    Background task to clean up expired sessions.
    """
    while True:
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, timestamp in session_timestamps.items()
            if current_time - timestamp > SESSION_TIMEOUT
        ]
        
        for session_id in expired_sessions:
            del chat_history[session_id]
            del session_timestamps[session_id]

        await asyncio.sleep(60)  # Run cleanup every 60 seconds

@app.on_event("startup")
async def startup_event():
    """
    Event handler to start background tasks.
    """
    asyncio.create_task(session_cleanup_task())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Use 0.0.0.0 to allow connections from external sources
        port=8000,
        reload=True,
        # log_level="debug"
    )
