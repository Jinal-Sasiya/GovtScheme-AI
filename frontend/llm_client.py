import os
from openai import AsyncOpenAI
from rag_engine import rag_engine
from dotenv import load_dotenv

load_dotenv(override=True)

# We use OpenAI library as a universal client. 
# You can set OPENAI_API_KEY and OPENAI_BASE_URL in your .env file
# to use local models (like Ollama/LMStudio) or other providers like OpenRouter/Groq.
api_key = os.getenv("OPENAI_API_KEY", "dummy_key")
base_url = os.getenv("OPENAI_BASE_URL", None)  # None defaults to standard OpenAI endpoint
model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url
)

SYSTEM_PROMPT = """You are "GovtScheme AI Copilot", an expert conversational AI assistant specialized in Indian Government Schemes. 

Your job is to answer user queries based ONLY on the provided context.
If no context is provided, or the context does not contain the answer, you MUST reply EXACTLY with:
"Sorry, I could not find reliable information related to your query."
DO NOT hallucinate or guess any scheme details.

Format your responses beautifully in Markdown.
Always try to use this structure if providing scheme details:
### [Scheme Name]
- **Eligibility:** ...
- **Benefits:** ...
- **State:** ...
- **Important Notes:** ...

Keep your responses clean, concise, and professional.
"""

class LLMClient:
    def __init__(self):
        # Conversational memory: dict mapping session_id to list of messages
        self.sessions = {}

    def get_session_history(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_session_history(session_id)
        history.append({"role": role, "content": content})
        
        # Keep only last 10 messages to avoid context window limits (1 system + 9 user/assistant)
        if len(history) > 10:
            self.sessions[session_id] = [history[0]] + history[-9:]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def chat_stream(self, session_id: str, query: str):
        # 1. Retrieve relevant schemes from FAISS
        retrieved = rag_engine.retrieve(query, top_k=3)
        context = rag_engine.format_context(retrieved)

        # 2. Add User Query + Context to history
        user_message = f"User Query: {query}"
        if context:
            user_message += f"\n\nContext Retrieved:\n{context}"
        else:
            user_message += "\n\nContext Retrieved:\nNone"

        # Note: We don't add the context-heavy prompt to the permanent memory to save space.
        # We only add the clean user query to memory, but for THIS request we send the context.
        history = self.get_session_history(session_id)
        
        # Build the messages array for the API call
        messages_for_api = history.copy()
        messages_for_api.append({"role": "user", "content": user_message})

        # Save just the clean query to memory
        self.add_message(session_id, "user", query)

        # 3. Handle low-confidence/no-context fallback
        # If retrieved is empty, it means all distances were > threshold
        if not retrieved:
            import ticket_system
            ticket_id = ticket_system.create_ticket(query)
            fallback_msg = f"Sorry, I could not find reliable information related to your query. A support ticket (**{ticket_id}**) has been automatically generated for our team to add this information."
            self.add_message(session_id, "assistant", fallback_msg)
            yield fallback_msg
            return

        # 4. Stream response from LLM
        try:
            stream = await client.chat.completions.create(
                model=model_name,
                messages=messages_for_api,
                stream=True,
                temperature=0.3
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    text_chunk = chunk.choices[0].delta.content
                    full_response += text_chunk
                    yield text_chunk
                    
            # Add assistant response to memory
            self.add_message(session_id, "assistant", full_response)
            
        except Exception as e:
            error_detail = str(e)
            print(f"LLM Error: {error_detail}")
            error_msg = f"Sorry, I encountered an error with the AI provider:\n\n{error_detail}"
            yield error_msg

llm_client = LLMClient()
