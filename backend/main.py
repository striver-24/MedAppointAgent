import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.tools import tool
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
load_dotenv()

app =FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the MedAppoint.io API! We are running Fine"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response_message = f"You said: {request.message}"
    return {"response": response_message}

@tool
def get_available_slots(speciality: str, day: str) -> list[str]:
    print(f"Fetching available slots for speciality: {speciality} on day: {day}...")
    try:
        requested_date = datetime.strptime(day, "%d-%m-%Y").date()
        if requested_date < date.today():
            return ["Error: I can book only future date appointments."]
        
    except ValueError:
        return ["Error: Date format should be DD-MM-YYYY."]