from fastapi import FastAPI, Response
from pydantic import BaseModel
from uvicorn import run
from typing import Dict

app = FastAPI()
users: Dict[int, Dict] = {}
xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<note>
  <to>User</to>
  <from>YATL</from>
  <heading>Reminder</heading>
  <body>Don't forget the meeting!</body>
</note>"""


class User(BaseModel):
    id: int
    name: str
    email: str


@app.post("/users")
def create_user(user: User):
    users[user.id] = {"name": user.name, "info": {"email": user.email}}
    return {"message": "User created"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return users.get(user_id, {"error": "User not found"})


@app.get("/xml")
def get_xml():
    return Response(content=xml_data, media_type="application/xml")


@app.post("/xml")
def post_xml(request: dict):
    # Echo back with XML
    return Response(content=xml_data, media_type="application/xml")


@app.get("/text")
def get_text():
    return Response(
        content="Hello, this is plain text response.", media_type="text/plain"
    )


@app.post("/text")
def post_text(request: dict):
    return Response(content="Received: " + str(request), media_type="text/plain")


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
