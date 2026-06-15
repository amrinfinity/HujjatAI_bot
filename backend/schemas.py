import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def sanitize_text(value: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value.strip())
    return cleaned


class PartyInfo(BaseModel):
    full_name: str = Field(..., min_length=1)
    birth_date: str = Field(..., min_length=1)
    passport: str = Field(..., min_length=1)
    pinfl: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    bank_details: Optional[str] = ""

    @field_validator("*", mode="before")
    @classmethod
    def clean_fields(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class MobileAppContractData(BaseModel):
    client: PartyInfo
    executor: PartyInfo

    project_name: str = Field(..., min_length=1)
    project_types: list[str] = Field(..., min_length=1)
    project_description: str = Field(..., min_length=1)
    technical_spec: Optional[str] = ""

    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    duration_days: int = Field(..., gt=0)

    total_amount: float = Field(..., gt=0)
    currency: str = Field(..., pattern="^(UZS|USD)$")
    advance_percent: float = Field(default=30, ge=0, le=100)
    advance_amount: float = Field(..., ge=0)
    final_percent: float = Field(default=70, ge=0, le=100)
    final_amount: float = Field(..., ge=0)
    payment_methods: list[str] = Field(..., min_length=1)
    penalty_percent: float = Field(default=0.1, ge=0)

    share_percent: float = Field(default=15, ge=0)
    share_years: int = Field(default=3, ge=1)
    report_period: str = Field(..., min_length=1)
    share_payment_date: str = Field(..., min_length=1)

    warranty_months: int = Field(default=12, ge=0)
    free_updates: int = Field(default=3, ge=0)
    response_days: int = Field(default=3, ge=0)

    ip_code_after_payment: bool = True
    ip_rights_until_payment: bool = True
    ip_github: bool = True
    ip_source_code: bool = True
    ip_database: bool = True
    ip_readme: bool = True

    nda_required: bool = True
    nda_years: int = Field(default=3, ge=0)

    acceptance_days: int = Field(default=10, ge=1)
    fix_days: int = Field(default=5, ge=1)

    contract_number: str = Field(..., min_length=1)
    contract_date: str = Field(..., min_length=1)
    contract_place: str = Field(..., min_length=1)
    electronic_signature: bool = False

    @field_validator(
        "project_name",
        "project_description",
        "technical_spec",
        "report_period",
        "share_payment_date",
        "contract_number",
        "contract_place",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class LegalEntityInfo(BaseModel):
    org_name: str = Field(..., min_length=1)
    stir: str = Field(..., pattern=r"^\d{9}$")
    mfy: str = Field(..., min_length=1)
    account_number: str = Field(..., min_length=1)
    bank_name: str = Field(..., min_length=1)
    legal_address: str = Field(..., min_length=1)
    actual_address: str = Field(..., min_length=1)
    director_name: str = Field(..., min_length=1)
    director_position: str = Field(default="Direktor")
    power_of_attorney: Optional[str] = ""
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)

    @field_validator("*", mode="before")
    @classmethod
    def clean_fields(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class IndividualPersonInfo(BaseModel):
    full_name: str = Field(..., min_length=1)
    birth_date: str = Field(..., min_length=1)
    passport: str = Field(..., min_length=1)
    pinfl: str = Field(..., pattern=r"^\d{14}$")
    address: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    card_number: str = Field(..., min_length=1)
    bank_name: str = Field(..., min_length=1)

    @field_validator("*", mode="before")
    @classmethod
    def clean_fields(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class IndividualLegalContractData(BaseModel):
    contract_type: str = Field(..., pattern="^(client_legal|client_individual)$")
    legal_entity: LegalEntityInfo
    individual: IndividualPersonInfo

    service_type: str = Field(..., min_length=1)
    service_description: str = Field(..., min_length=1)
    work_scope: str = Field(..., min_length=1)

    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    duration_days: int = Field(..., gt=0)

    total_amount: float = Field(..., gt=0)
    currency: str = Field(..., pattern="^(UZS|USD)$")
    advance_percent: float = Field(default=50, ge=0, le=100)
    advance_amount: float = Field(..., ge=0)
    final_amount: float = Field(..., ge=0)
    payment_methods: list[str] = Field(..., min_length=1)
    penalty_percent: float = Field(default=0.1, ge=0)

    nda_required: bool = True
    nda_years: int = Field(default=2, ge=0)
    warranty_months: int = Field(default=6, ge=0)
    liability_limit: str = Field(..., min_length=1)

    contract_number: str = Field(..., min_length=1)
    contract_date: str = Field(..., min_length=1)
    contract_place: str = Field(..., min_length=1)

    @field_validator(
        "service_type",
        "service_description",
        "work_scope",
        "liability_limit",
        "contract_number",
        "contract_place",
        mode="before",
    )
    @classmethod
    def clean_strings_individual_legal(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class LegalPartyFull(BaseModel):
    org_name: str = Field(..., min_length=1)
    org_form: str = Field(..., pattern="^(MChJ|OAJ|QK|YT)$")
    stir: str = Field(..., pattern=r"^\d{9}$")
    mfy: str = Field(..., min_length=1)
    oked: Optional[str] = ""
    account_number: str = Field(..., min_length=1)
    bank_name: str = Field(..., min_length=1)
    mfo: str = Field(..., min_length=1)
    legal_address: str = Field(..., min_length=1)
    actual_address: str = Field(..., min_length=1)
    director_name: str = Field(..., min_length=1)
    director_position: str = Field(default="Direktor")
    power_of_attorney: Optional[str] = ""
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    website: Optional[str] = ""

    @field_validator("*", mode="before")
    @classmethod
    def clean_party_fields(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class PaymentStage(BaseModel):
    name: str = Field(..., min_length=1)
    percent: float = Field(..., ge=0, le=100)
    amount: float = Field(..., ge=0)
    condition: str = Field(..., min_length=1)


class LegalLegalContractData(BaseModel):
    party_first: LegalPartyFull
    party_second: LegalPartyFull

    service_type: str = Field(..., min_length=1)
    service_description: str = Field(..., min_length=1)
    work_scope: str = Field(..., min_length=1)
    has_technical_spec: bool = False

    effective_date: str = Field(..., min_length=1)
    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    duration_days: int = Field(..., gt=0)
    contract_term: str = Field(..., min_length=1)

    total_amount: float = Field(..., gt=0)
    currency: str = Field(..., pattern="^(UZS|USD|EUR)$")
    payment_type: str = Field(..., pattern="^(one_time|staged|monthly)$")
    stages_count: int = Field(default=1, ge=1)
    payment_stages: list[PaymentStage] = Field(..., min_length=1)
    advance_percent: float = Field(default=30, ge=0, le=100)
    advance_amount: float = Field(..., ge=0)
    final_amount: float = Field(..., ge=0)
    payment_methods: list[str] = Field(..., min_length=1)
    penalty_percent: float = Field(default=0.1, ge=0)
    penalty_max_days: int = Field(default=30, ge=0)

    quality_standard: str = Field(..., min_length=1)
    acceptance_days: int = Field(default=10, ge=1)
    fix_days: int = Field(default=5, ge=1)
    acceptance_act_required: bool = True

    liability_limit: str = Field(..., min_length=1)
    warranty_months: int = Field(default=12, ge=0)
    free_fixes: int = Field(default=3, ge=0)
    insurance_required: bool = False

    nda_required: bool = True
    nda_years: int = Field(default=3, ge=0)
    ip_owner: str = Field(..., pattern="^(party_first|party_second|joint)$")
    repository_transfer: bool = False

    contract_number: str = Field(..., min_length=1)
    contract_date: str = Field(..., min_length=1)
    contract_place: str = Field(..., min_length=1)
    copies_count: int = Field(default=2, ge=1)
    electronic_signature: bool = False

    @field_validator(
        "service_type",
        "service_description",
        "work_scope",
        "contract_term",
        "quality_standard",
        "liability_limit",
        "contract_number",
        "contract_place",
        mode="before",
    )
    @classmethod
    def clean_legal_legal_strings(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class RentalPersonInfo(BaseModel):
    full_name: str = Field(..., min_length=1)
    birth_date: str = Field(..., min_length=1)
    passport: str = Field(..., min_length=1)
    pinfl: str = Field(..., pattern=r"^\d{14}$")
    address: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    property_document: Optional[str] = ""
    workplace: Optional[str] = ""

    @field_validator("*", mode="before")
    @classmethod
    def clean_rental_person(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class RentalContractData(BaseModel):
    contract_number: str = Field(..., min_length=1)
    contract_date: str = Field(..., min_length=1)
    contract_place: str = Field(..., min_length=1)
    rental_period: str = Field(..., min_length=1)

    landlord: RentalPersonInfo
    tenant: RentalPersonInfo

    property_address: str = Field(..., min_length=1)
    property_type: str = Field(..., min_length=1)
    total_area: float = Field(..., gt=0)
    rooms_count: int = Field(..., ge=1)
    floor: int = Field(..., ge=0)
    furnished: bool = False
    appliances: list[str] = Field(default_factory=list)
    other_appliances: Optional[str] = ""

    monthly_rent: float = Field(..., gt=0)
    currency: str = Field(..., pattern="^(UZS|USD)$")
    deposit: float = Field(..., ge=0)
    payment_day: str = Field(..., min_length=1)
    payment_methods: list[str] = Field(..., min_length=1)
    utilities_paid_by: list[str] = Field(..., min_length=1)
    utilities_note: Optional[str] = ""
    penalty_percent: float = Field(default=0.5, ge=0)

    pets_allowed: str = Field(..., min_length=1)
    guests_policy: str = Field(..., min_length=1)
    smoking_policy: str = Field(..., min_length=1)
    repairs_by: str = Field(..., min_length=1)
    max_repair_amount: Optional[float] = None

    deposit_return_terms: str = Field(..., min_length=1)
    notice_days: int = Field(default=30, ge=1)
    early_termination_penalty: Optional[float] = None
    damage_liability: str = Field(..., min_length=1)

    electronic_signature: bool = False
    witnesses_required: bool = False
    witnesses_count: int = Field(default=2, ge=0)

    @field_validator(
        "contract_number",
        "contract_place",
        "property_address",
        "deposit_return_terms",
        "damage_liability",
        "other_appliances",
        "utilities_note",
        mode="before",
    )
    @classmethod
    def clean_rental_strings(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class ActItem(BaseModel):
    number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    total: float = Field(..., ge=0)

    @field_validator("description", "unit", mode="before")
    @classmethod
    def clean_act_item(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value


class ActData(BaseModel):
    act_number: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    contract_number: str = Field(..., min_length=1)
    contract_date: str = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=1)
    executor_name: str = Field(..., min_length=1)
    items: list[ActItem] = Field(..., min_length=1)
    grand_total: float = Field(..., gt=0)
    grand_total_words: Optional[str] = ""
    quality_status: str = Field(..., min_length=1)
    has_claims: str = Field(..., min_length=1)
    claims_details: Optional[str] = None

    @field_validator(
        "act_number",
        "city",
        "contract_number",
        "customer_name",
        "executor_name",
        "grand_total_words",
        "quality_status",
        "has_claims",
        "claims_details",
        mode="before",
    )
    @classmethod
    def clean_act_strings(cls, value):
        if isinstance(value, str):
            return sanitize_text(value)
        return value
