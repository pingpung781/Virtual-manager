from fastapi import FastAPI

app = FastAPI(title="Virtual AI Manager", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Virtual AI Manager System Online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
