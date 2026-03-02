from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
import uvicorn
from fastapi.exceptions import HTTPException

app = FastAPI()
users = []


class User(BaseModel):
    name: str
    email: EmailStr


@app.post("/users")
def create_user(user: User, response_code: int = 201):
    id = len(users) + 1
    users.append((id, user.name, user.email))
    return {"user_id": id}


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    for user in users:
        if user[0] == user_id:
            return {"name": user[1], "email": user[2]}


@app.delete("/users/{user_id}")
def delete_user_by_id(user_id: int):
    delete_id = None
    for id, user in enumerate(users):
        if user[0] == user_id:
            delete_id = id

    if delete_id is None:
        raise HTTPException(status_code=404, detail="User not found")

    users.pop(delete_id)
    return {"status": "User deleted"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
