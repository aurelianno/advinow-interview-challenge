from fastapi import FastAPI
from app.views import router     

# Initialize the FastAPI app with a clear title and version
app = FastAPI(title="AdviNow Interview Challenge", version="1.6")

# Include our router so both endpoints are available
app.include_router(router)

# If run directly, start Uvicorn with reload for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.run:app", host="127.0.0.1", port=8013, reload=True)