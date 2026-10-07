from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, StringConstraints
from typing import Annotated
import secrets
import string

app = FastAPI()

#### UTILS


def generate_string(length: int) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


### DB

tmp_db = {
    "url_to_code": {},
    "code_to_url": {},  # short_code: orig_url
    "reserved_codes": ("docs", "redoc", "shorten", "admin", "openapi.json", "health"),
}

## PYDANTIC MODELS


class Payload(BaseModel):
    url: HttpUrl
    custom_code: (
        Annotated[
            str, StringConstraints(min_length=3, max_length=16, pattern=r"^[a-z0-9]+$")
        ]
    ) | None = None
    # I made that the generated codes are always small letters to minimize confusion if the
    # end user have to type it from memory. (and to avoid colision bugs caused by case insesitivity.)


class ResponseModel(BaseModel):
    short_url: HttpUrl
    code: str
    original_url: HttpUrl
    created: bool


## ENDPOINTS


@app.post("/shorten", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def shortener(payload: Payload):
    code = payload.custom_code
    url = str(payload.url)
    if url in tmp_db["url_to_code"]:
        return ResponseModel(
            short_url=f"http://localhost:8000/{tmp_db['url_to_code'][url]}",
            code=tmp_db["url_to_code"][url],
            original_url=url,
            created=False,
        )
    # this tiny if statment right here does all the idepotency of the urls sent to the
    # app and it added new ones to it's db, but forbid duplication of existing ones.

    if payload.custom_code in tmp_db["reserved_codes"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Short code reserved"
        )

    if payload.custom_code in tmp_db["code_to_url"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Short code already taken"
        )
    if not code:
        code = generate_string(6)
        while code in tmp_db["code_to_url"]:
            code = generate_string(6)
            # this while loop is to avoid collisions in the generated codes, but
            # the chances of that happening are very low.
            # the digit limit for out generated codes is 6, which gives us 36^6 = 2,176,782,336 possible combinations.
            # which is designed to be enough for a small scale url shortener.

    tmp_db["url_to_code"][url] = code
    tmp_db["code_to_url"][code] = url

    response = ResponseModel(
        short_url=f"http://localhost:8000/{code}",
        code=code,
        original_url=url,
        created=True,
    )
    return response


# Removed trailing slash from the endpoint to
# avoid confusion and because the short url has to be exact.
@app.get("/{code}")
def redirector(code: str):
    if code in tmp_db["code_to_url"]:
        return RedirectResponse(
            url=tmp_db["code_to_url"][code],
            status_code=status.HTTP_302_FOUND,
        )
    # learned this recently that a browser does caching and other operations based on the status
    # code it recieves so to not "poison" the user cache we'll use a simple 302.
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short code not found"
        )
