import uvicorn
from fastapi import FastAPI
from backend.api.v1 import resume
from backend.api.v1 import auth
app = FastAPI()
app.include_router(auth.router,   prefix="/api/v1/auth")
app.include_router(resume.router,   prefix="/api/v1/resume")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)

