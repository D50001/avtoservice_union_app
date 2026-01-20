import json
import os
import re
from typing import Any

from pydantic import ValidationError

from .schemas import (
    CompanyLeaderForm,
    IndividualEntrepreneurForm,
    LegalEntityForm
)
from logger import logger

from ms_word.services import MSWordManager
from mail.services import EmailManager
from amo.services import AmoCRMManager
from settings import settings


def fix_bad_json(bad_json_bytes):
    bad_json_str = bad_json_bytes.decode('utf-8')

    fixed_json_str = bad_json_str.replace('\\"', '"')

    fixed_json_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', '', fixed_json_str)

    return fixed_json_str


def parse_maybe_double_json(raw: bytes) -> dict | None:
    try:
        text = raw.decode("utf-8").strip()
        data = json.loads(text)

        # если после первого loads это строка — грузим ещё раз
        if isinstance(data, str):
            data = json.loads(data)

        return data

    except Exception:
        logger.exception("Failed to parse payload")
        return None

async def process_data(data: Any):
    data_type = detect_form_type(data)
    logger.info(data_type)
    try:
        serialized_data = data_type(**data)
        logger.info(f"Successfully validated: {serialized_data}")
    except ValidationError as e:
        logger.error(e)
        logger.warning(f"Сan not validate data: {data}")
        return
    word = MSWordManager()
    if data_type == CompanyLeaderForm:
        participation_form = word.create_leader_participation_form(serialized_data)
    if data_type == IndividualEntrepreneurForm:
        participation_form = word.create_individual_entrepreneur_participation_form(serialized_data)
    if data_type == LegalEntityForm:
        participation_form = word.create_legal_entity_participation_form(serialized_data)
    principle = word.create_principle(serialized_data)
    survey_form = word.create_survey_form(serialized_data)
    personal_data_consent = word.create_personal_data_consent(serialized_data)

    email_manager = EmailManager()
    if serialized_data.email:
        try:
            response = await email_manager.send_participation_email(
                #serialized_data.email,
                settings.ADMIN_EMAIL_ADDRESS,
                participation_form,
                survey_form,
                principle,
                personal_data_consent
            )
            logger.info(response)
        except Exception as e:
            logger.warning(f"Email sent error: {e}")

        try:
            response = await email_manager.send_confirmation_email(
                serialized_data.email
            )
            logger.info(response)
        except Exception as e:
            logger.warning(f"Email sent error: {e}")

    amo_crm_manager = AmoCRMManager()
    response = await amo_crm_manager.send_lead_to_amo(serialized_data)
    logger.info(response)


def detect_form_type(data: dict) -> type:
    status = data.get("В каком статусе вы планируете участвовать в деятельности Союза?", "")

    if "Юридическое лицо" in status:
        return LegalEntityForm
    elif "Физическое лицо" in status:
        return CompanyLeaderForm
    elif "Индивидуальный предприниматель" in status:
        return IndividualEntrepreneurForm
    else:
        raise ValueError("Неизвестный тип данных")