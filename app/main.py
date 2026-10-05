from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, StringConstraints
from typing import Annotated
import secrets
import string

app = FastAPI()

#### UTILS


def generate_string(length: int) -> str:
    if length < 0:
        raise ValueError("Length must be non-negative")

    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


### DB

tmp_db = {
    "taken_urls": {},
    "reserved_codes": ("docs", "redoc", "shorten", "admin", "openapi.json"),
}

## PYDANTIC MODELS


class Payload(BaseModel):
    url: HttpUrl
    custom_code: (
        Annotated[str, StringConstraints(max_length=6, pattern=r"^[a-z0-9]*$")]
    ) | None = None


class ResponseModel(BaseModel):
    short_url: HttpUrl
    code: str
    original_url: HttpUrl
    created: bool


## ENDPOINTS


@app.post("/shorten", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def shortener(payload: Payload):
    if str(payload.custom_code) in tmp_db["taken_urls"].keys():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Short code already taken"
        )
    elif str(payload.custom_code) in tmp_db["reserved_codes"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Short code reserved"
        )
    if not payload.custom_code:
        payload.custom_code = generate_string(6)
        while str(payload.custom_code) in tmp_db["taken_urls"].keys():
            payload.custom_code = generate_string(6)

    tmp_db["taken_urls"][str(payload.custom_code)] = str(payload.url)

    response = ResponseModel(
        short_url=f"http://localhost:8000/{payload.custom_code}",
        code=payload.custom_code,
        original_url=payload.url,
        created=True,
    )
    return response


@app.get("/{code}")
def redirector(code: str):
    if code in tmp_db["taken_urls"].keys():
        return RedirectResponse(
            url=tmp_db["taken_urls"][code],
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short code not found"
        )
