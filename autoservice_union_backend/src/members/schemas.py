import re

from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_validator, ConfigDict, model_validator, validator
from typing import Optional, Union, Any
from datetime import datetime
from logger import logger


class BankDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bank_name: Optional[str] = Field(None, alias="Наименование банка")
    account_number: Optional[str] = Field(None, alias="Расчетный счет")
    correspondent_account: Optional[str] = Field(None, alias="Корреспондентский счет")
    bik: Optional[str] = Field(None, alias="БИК")


class RepresentativeInfo(BaseModel):
    position: Optional[str] = Field(None, description="Должность сотрудника")
    name: Optional[str] = Field(None, description="ФИО сотрудника")
    email: Optional[str] = Field(None, description="Электронная почта")
    phone: Optional[str] = Field(None, description="Телефон")
    power_of_attorney_number: Optional[str] = Field(None, description="Номер доверенности")
    power_of_attorney_date: Optional[str] = Field(None, description="Дата выдачи доверенности")
    power_of_attorney_place: Optional[str] = Field(None, description="Место выдачи доверенности")
    power_of_attorney_validity: Optional[str] = Field(None, description="Срок действия доверенности")


class AutoServiceUnionForm(BaseModel):
    model_config = ConfigDict(extra='ignore')

    full_name: str = Field(..., alias="Ваши фамилия, имя и отчество")
    participation_status: str = Field(..., alias="В каком статусе вы планируете участвовать в деятельности Союза?")

    payment_confirmation: Optional[HttpUrl] = Field(None,
                                                    alias="Пожалуйста загрузите подтверждение оплаты вступительного взноса")
    passport_data: Optional[str] = Field(None, alias="Паспортные данные (серия, номер, дата выдачи, выдавший орган)")
    registration_address: Optional[str] = Field(None, alias="Адрес по прописке с индексом")
    ogrnip: Optional[str] = Field(None, alias="ОГРНИП")
    company_inn: Optional[str] = Field(None, alias="ИНН организации")

    tax_registration_date: Optional[Union[datetime,str]] = Field(None, alias="Дата постановки на учет в налоговом органе")
    registration_date: Optional[Union[datetime,str]] = Field(None, alias="Дата регистрации организации / ИП")

    legal_address: Optional[str] = Field(None, alias="Адрес организации юридический")
    actual_address: Optional[str] = Field(None, alias="Адрес места основной деятельности организации")
    mailing_address: Optional[str] = Field(None, alias="Адрес для почтовой корреспонденции с индексом")
    company_phone: str = Field(..., alias="Телефон 1 организации / ИП")
    personal_phone: str = Field(..., alias="Телефон личный в формате +7ХХХХХХХХХХ")
    website: Optional[str] = Field(None, alias="Адрес сайта")
    email: EmailStr = Field(..., alias="Е-мейл организации / ИП")

    bank_details: Optional[BankDetails] = Field(None, exclude=True)  # exclude=True, чтобы не искать его в исходном JSON
    locations: Optional[str] = Field(None, alias="В каких городах и населенных пунктах работает ваше предприятие")
    employee_count: Optional[str] = Field(None, alias="Среднесписочная численность организации")
    service_points_count: Optional[str] = Field(None, alias="Количество сервисов и ремонтных постов в каждом из них")
    service_zones_photos: Optional[HttpUrl] = Field(None, alias="Приложите фотографии: ремонтной зоны, зону приёмки...")
    facilities: Optional[str] = Field(None, alias="Имеете ли при сервисе, даже если это не ваш бизнес:")
    specialization: Optional[str] = Field(None, alias="Какова специализация вашей организации?")
    okved_codes: Optional[str] = Field(None, alias="Основные коды ОКВЭД организации / ИП")
    company_ogrnip: Optional[str] = Field(None, alias="ОГРНИП"
                                          )
    interaction_method: Optional[str] = Field(None, alias="Как будете взаимодействовать с Союзом")
    representative: Optional[str] = Field(
        None,
        alias="Сотрудник, ответственный за взаимодействие с Союзом (по доверенности)"
    )
    social_media: Optional[str] = Field(
        None,
        alias="Укажите ваше представительство в интернете"
    )

    participation_purpose: Optional[str] = Field(None,
                                                 alias="Какова цель участия в Союзе автосервисов вас / вашей организации")
    interested_services: Optional[str] = Field(None, alias="В каких услугах Вы заинтересованы:")
    can_help_with: Optional[str] = Field(None, alias="Чем можете быть полезны...")
    recommended_partners: Optional[str] = Field(
        None,
        alias="Кого бы Вы рекомендовали в качестве добросовестного партнера..."
    )
    consent_to_personal_data_processing: Optional[str] = Field(None, alias="Даю свое согласие на обработку персональных данных")
    data_accuracy_confirmation: Optional[str] = Field(None, alias="Достоверность данных подтверждаю")
    submission_date: str = Field(..., alias="Дата заполнения регистрационной формы")

    @model_validator(mode='before')
    @classmethod
    def assemble_bank_details(cls, data):
        if not isinstance(data, dict):
            return data

        bank_data = {
            "bank_name": data.get("Наименование банка"),
            "account_number": data.get("Расчетный счет"),
            "correspondent_account": data.get("Корреспондентский счет"),
            "bik": data.get("БИК")
        }
        condition_met = all(value and value not in [None, "Нет ответа"] for value in bank_data.values())

        if condition_met:
            data['bank_details'] = bank_data
        else:
            data['bank_details'] = None

        return data

    @field_validator(
        'tax_registration_date',
        'registration_date',
        'registration_address',
        mode='before'
    )
    def parse_dates(cls, v):
        if v in (None, "Нет ответа"):
            return None
        try:
            return datetime.strptime(v, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(v, '%d.%m.%Y').date()
            except ValueError:
                return v

    @field_validator("representative", mode='before')
    def set_representative(cls, v):
        if v in (None, "Нет ответа"):
            return None
        try:
            return v
        except (ValueError, AttributeError):
            return None

    @field_validator("social_media", mode='before')
    def set_social_media(cls, v, values):
        if v in (None, "Нет ответа"):
            return None
        return v.replace('\\n', '\n').replace('Укажите ваше представительство в интернете', '')

    @field_validator('company_ogrnip', 'company_inn', mode='before')
    def parse_ogrnip_and_inn(cls, v):
        return None if v == "Нет ответа" else v

    @field_validator('representative', mode='before')
    def parse_representative(cls, value):
        if not value or not isinstance(value, str):
            return value

        data = {}
        lines = value.split("\\n")
        try:
            data["position"] = lines[1].replace('Должность сотрудника - ', '')
            data["name"] = lines[2].replace('Фамилия, имя и отчество - ', '')
            data["email"] = lines[3].replace('Е-мейл - ', '')
            data["phone"] = lines[4].replace('Телефон - ', '')
        except IndexError as e:
            logger.info(e)

        cls._representative_info = RepresentativeInfo(**data)
        return value

    @property
    def representative_info(self) -> RepresentativeInfo:
        return getattr(self, "_representative_info", None)


class CompanyLeaderForm(AutoServiceUnionForm):
    company_name: Optional[str] = Field(None, alias="Полное название организации")
    company_short_name: Optional[str] = Field(None, alias="Сокращенное название организации")
    company_kpp: Optional[str] = Field(None, alias="КПП")
    company_ogrn: Optional[str] = Field(None, alias="ОГРН организации")


    @field_validator(
        'company_ogrn',
        'company_kpp',
        'company_name',
        mode='before'
    )
    def empty_to_none(cls, v):
        return None if v == "Нет ответа" else v


class LegalEntityForm(AutoServiceUnionForm):
    company_name: Optional[str] = Field(None, alias="Полное название организации")
    company_short_name: Optional[str] = Field(None, alias="Сокращенное название организации")
    company_kpp: Optional[str] = Field(None, alias="КПП")
    company_ogrn: Optional[str] = Field(None, alias="ОГРН организации")

    director_position: Optional[str] = Field(None, alias="Должность руководителя организации")
    director_full_name: Optional[str] = Field(None, alias="Фамилия, имя, отчество руководителя организации")
    representative_documents: Optional[str] = Field(
        None,
        alias="Документы, наделяющие вас правом представлять организацию в Союзе автосервисов"
    )

    okved: Optional[str] = Field(None, alias="Основные коды ОКВЭД организации / ИП")


    @field_validator('company_ogrn', 'company_ogrnip', 'company_inn', 'company_kpp', mode='before')
    def empty_to_none(cls, v):
        return None if v == "Нет ответа" else v


class IndividualEntrepreneurForm(AutoServiceUnionForm):
    pass
