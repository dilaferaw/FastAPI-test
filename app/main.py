from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl, StringConstraints
from typing import Annotated

app = FastAPI()

tmp_db = {"taken_urls": []}


class Payload(BaseModel):
    url: HttpUrl
    custom_code: Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+$")]


class ResponseModel(BaseModel):
    short_url: HttpUrl
    code: str
    original_url: HttpUrl
    created: True


@app.post("/shorten", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def shortener(payload: Payload):
    if str(payload.url) in tmp_db["taken_urls"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="URL already taken"
        )

    tmp_db["taken_urls"].append(str(payload.url))
    return {"help": "this is insane"}
