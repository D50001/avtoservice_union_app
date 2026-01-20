import json
from typing import Union

from fastapi import APIRouter, Depends
from starlette.background import BackgroundTask
from starlette.requests import Request

from logger import logger
from starlette.responses import JSONResponse

from .services import (
    parse_maybe_double_json,
    process_data,
    parse_yandex_forms_payload
)



router = APIRouter(
    prefix="",
    tags=["survey"]
)


@router.post("/")
async def create_member(request: Request):
    background_task = None

    try:
        raw = await request.body()
        logger.info("Received raw data: %r", raw)

        payload = parse_yandex_forms_payload(raw)

        if payload:
            background_task = BackgroundTask(process_data, payload)

    except Exception as e:
        logger.exception(f"Unexpected error {e}")

    # подписка не отваливается
    return JSONResponse({"ok": True}, status_code=200, background=background_task)
