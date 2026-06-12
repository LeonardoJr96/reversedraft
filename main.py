from fastapi import FastAPI


from src.api.sofifa import get_league_info

app = FastAPI(title="ReverseDraft")

@app.get("/")
def root():
    return {"message": get_league_info()}