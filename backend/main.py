# Web Socket App

import asyncio
import time
import os
from dotenv import load_dotenv
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect

from agent import ProfessorRaterAgent
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# CONSTANTS
SECRET_KEY = os.getenv("SECRET_KEY", "S@MPL3")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 60))

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
async def get(request: Request, response: Response):
    """
    Serve the chat interface and manage session state.
    """
    print("GET request received. Checking session state...")  # Debug message

    # Retrieve session ID from cookies
    session_id = request.cookies.get("session_id")
    print(f"Session ID from cookie: {session_id}")  # Debug message
    
    if session_id in session_timestamps:
        if time.time() - session_timestamps[session_id] > SESSION_TIMEOUT:
            # If session has timed out, clear the history and delete the session
            print(f"Session {session_id} timed out. Clearing session data.")  # Debug message
            del chat_history[session_id]
            del session_timestamps[session_id]
            session_id = None
        else:
            print(f"Session {session_id} is active.")  # Debug message
    else:
        print("No valid session found. Generating a new session ID.")  # Debug message

    # Generate a new session ID if necessary
    if not session_id:
        session_id = str(uuid4())
        print(f"New session ID generated: {session_id}")  # Debug message
   
    # Set the session ID in cookies
    response.set_cookie(key="session_id", value=session_id)
    print(f"Session ID set in cookie: {session_id}")  # Debug message
    
    # Update the session timestamp and chat history
    session_timestamps[session_id] = time.time()
    if session_id not in chat_history:
        chat_history[session_id] = []
        print(f"Chat history initialized for session {session_id}.")  # Debug message
    
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling real-time chat messages.
    """
    print("WebSocket connection attempt.")  # Debug message

    # Accept the WebSocket connection
    await websocket.accept()
    print("WebSocket connection accepted.")  # Debug message
    
    # Extract session ID from initial handshake
    session_id = websocket.cookies.get("session_id")
    print(f"Session ID from WebSocket cookies: {session_id}")  # Debug message
    
    if not session_id:
        print("Session ID not found in WebSocket cookies. Closing connection.")  # Debug message
        await websocket.close()
        return
    
    try:
        while True:
            # Receive and process messages
            print(f"Waiting for message from session {session_id}...")  # Debug message
            human_message = await websocket.receive_text()
            print(f"Received message from session {session_id}: {human_message}")  # Debug message
            
            # Generate AI response
            ai_response = agent.invoke(human_message, chat_history[session_id])
            print(f"AI response generated for session {session_id}: {ai_response}")  # Debug message
            
            # Update chat history and last activity timestamp
            chat_history[session_id].append(HumanMessage(human_message))
            chat_history[session_id].append(AIMessage(ai_response))
            session_timestamps[session_id] = time.time()
            print(f"Chat history and timestamp updated for session {session_id}.")  # Debug message
            
            await websocket.send_text(ai_response) 
            print(f"Response sent to session {session_id}.")  # Debug message

    except WebSocketDisconnect:
        # Handle WebSocket disconnection
        print(f"Session {session_id} disconnected.")  # Debug message

async def session_cleanup_task():
    """
    Background task to clean up expired sessions.
    """
    print("Starting session cleanup task...")  # Debug message

    while True:
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, timestamp in session_timestamps.items()
            if current_time - timestamp > SESSION_TIMEOUT
        ]
        
        for session_id in expired_sessions:
            print(f"Cleaning up expired session {session_id}.")  # Debug message
            if session_id in chat_history:
                del chat_history[session_id]
            if session_id in session_timestamps:
                del session_timestamps[session_id]

        print("Session cleanup task completed. Sleeping for 60 seconds...")  # Debug message
        await asyncio.sleep(60)  # Run cleanup every 60 seconds

@app.on_event("startup")
async def startup_event():
    """
    Event handler to start background tasks.
    """
    print("Application startup: Starting background tasks...")  # Debug message
    asyncio.create_task(session_cleanup_task())

if __name__ == "__main__":
    import uvicorn
    print("Starting WebSocket app with Uvicorn...")  # Debug message
    uvicorn.run(app, host="localhost", port=8000, reload=True)
