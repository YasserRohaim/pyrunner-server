from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, root_validator, ValidationError
from uuid import UUID, uuid4
from runner import send_command, spawn_python_shell
import logging
import os
from typing import Optional

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store the processes for each user
procs = {}

# Define the request model for input, where session_id is a UUID
class CodeRequest(BaseModel):
    id: UUID = None
    code: str

# Define the response model
class CodeResponse(BaseModel):
    id: UUID
    stdout: Optional[str] = Field( description="Standard output of the code execution")
    stderr: Optional[str] = Field( description="Standard error of the code execution")
    error: Optional[str] = Field(description="Error message if execution fails")

   
@app.post("/execute")
async def execute_code(request: CodeRequest):
    try:
        if request.id is None:
            id = uuid4()
            process, master = spawn_python_shell()
            procs[id] = (process, master)
        else:
            if request.id not in procs:
                return JSONResponse(status_code=404,
                                content={"error":"Session not found"}) 
            process, master = procs[request.id]
            if  process.poll():
                procs.pop(request.id)
                return JSONResponse(status_code=404,content={"error": "process is dead"})

        result = send_command(process, master, request.code)
        result["id"] = request.id if request.id else id

        return result
    except HTTPException as he:
        raise he
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        print(e)
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)