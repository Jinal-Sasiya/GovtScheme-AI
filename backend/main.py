from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from llm_client import llm_client
import ticket_system

# Initialize the ticket database
ticket_system.init_db()

app = FastAPI(title="GovtScheme AI Copilot API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    query: str

class ClearMemoryRequest(BaseModel):
    session_id: str

@app.get("/")
def read_root():
    return {"message": "Welcome to GovtScheme AI Copilot API"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Returns a streaming response using Server-Sent Events (SSE).
    """
    async def event_generator():
        async for chunk in llm_client.chat_stream(request.session_id, request.query):
            # Yielding in SSE format (Server-Sent Events) for easy consumption on frontend
            # The format is typically: data: {content}\n\n
            # For simplicity, we just yield the text chunk, and the frontend will piece it together
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/clear_memory")
def clear_memory(request: ClearMemoryRequest):
    llm_client.clear_session(request.session_id)
    return {"status": "success", "message": "Memory cleared."}

@app.get("/api/tickets")
def get_tickets():
    """
    Returns all logged tickets.
    """
    tickets = ticket_system.get_all_tickets()
    return {"status": "success", "total": len(tickets), "tickets": tickets}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
