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

system_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful and friendly medical appointment booking assistant.
            
            Your capabilities are:
            1. Checking for available appointment slots for a specific specialty and future date.
            2. Booking an appointment for a user.

            Your instructions are:
            - Today's date is {today}. Do not use tools for today's date.
            - Before booking an appointment, you MUST have the patient's full name. If you don't have it, you must ask for it.
            - Do not ask for any personal information other than the patient's name.
            - When a user asks for available slots, use the `get_available_slots` tool.
            - When a user confirms they want to book a specific slot, use the `book_appointment` tool.
            - Respond in a clear, conversational, and professional manner.
            """,
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
).partial(today=date.today())


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    inputs = {"messages": [HumanMessage(content=request.message)]}
    final_response = ""
    for chunk in app_graph.stream(inputs):
        if "agent" in chunk:
            for message in chunk["agent"]["messages"]:
                final_response += str(message.content)
    
    return {"response": final_response}

@tool
def get_available_slots(speciality: str, day: str) -> list[str]:
    print(f"Fetching available slots for speciality: {speciality} on day: {day}...")
    try:
        requested_date = datetime.strptime(day, "%d-%m-%Y").date()
        if requested_date < date.today():
            return ["Error: I can book only future date appointments."]
        
        if "Cardiology" in speciality:
            slots = ["10:00 AM", "11:00 AM", "02:00 PM"]
        elif "Dermatology" in speciality:
            slots = ["09:00 AM", "01:00 PM", "03:00 PM"]
        elif "Neurology" in speciality:
            slots = ["10:30 AM", "12:30 PM", "04:00 PM"]
    except ValueError:
        return ["Error: Date format should be DD-MM-YYYY."]
    
@tool
def book_appointment(speciality: str, day: str, time: str, patient_name: str) -> str:
    print(f"Booking appointment for {patient_name} with {speciality} on {day} at {time}..")
    return f"Appointment booked for {patient_name} with {speciality} on {day} at {time}."

tools = [get_available_slots, book_appointment]

# Agent State and Graph using Langgraph
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

llm = ChatGroq(model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    print("Calling Model....")
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

def call_tool(state: AgentState):
    print("Calling Tool....")
    last_message = state['message'][-1]

    tool_outputs = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name']
        selected_tool = next(t for t in tools if t.name == tool_name)
        output = selected_tool.invoke(tool_call['args'])
        tool_outputs.append(output)

    from langchain_core.messages import ToolMessage
    tool_messages = [ToolMessage(content=str(output), tool_call_id=call['id'])
                     for call, output in zip(last_message.tool_calls, tool_outputs)]
    return {"messages": tool_messages}

def should_continue(state: AgentState):
    print("Checking for the tool calls....")
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "action"
    else:
        return END
    

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"action": "action", END: END}
)

workflow.add_edge("action", "agent")

add_graph = workflow.compile()
print("Graph Compiled Succesfully!")

