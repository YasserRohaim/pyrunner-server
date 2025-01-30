from fastapi import FastAPI
from pydantic import BaseModel
from uuid import UUID

app = FastAPI()

# Define the request model for input, where session_id is a UUID
class CodeRequest(BaseModel):
    id: UUID
    code: str

@app.post("/execute")
async def execute_code(request: CodeRequest):
    
    print(f"Session ID: {request.session_id}")
    print(f"Code: {request.code}")
    
    return {"message": "Code executed successfully", "session_id": str(request.session_id)}

