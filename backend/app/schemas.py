from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ShoppingMode(StrEnum):
    PRIVATE = "PRIVATE"
    STAFF_ASSISTED = "STAFF_ASSISTED"


class CheckinStatus(StrEnum):
    CHECKED_IN = "CHECKED_IN"
    SELF_SHOPPING = "SELF_SHOPPING"
    WAITING_FOR_STAFF = "WAITING_FOR_STAFF"
    ASSIGNED = "ASSIGNED"
    SERVING = "SERVING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class VisitPurposeCode(StrEnum):
    GIFT = "GIFT"
    SEASON_UPDATE = "SEASON_UPDATE"
    SPECIAL_EVENT = "SPECIAL_EVENT"
    BUSINESS_TRIP = "BUSINESS_TRIP"
    FREE_SHOPPING = "FREE_SHOPPING"
    OTHER = "OTHER"


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"


class EntryChannel(StrEnum):
    QR = "QR"
    NFC = "NFC"


class LoginRequest(ApiModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=4, max_length=200)


class CustomerSignupRequest(ApiModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=13, pattern=r"^01[016789]-?\d{3,4}-?\d{4}$")
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=4, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("이름은 2자 이상이어야 합니다.")
        return normalized

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return value.replace("-", "")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class StaffSignupRequest(ApiModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=4, max_length=200)
    store_id: str = Field(min_length=2, max_length=32)
    signup_code: str = Field(min_length=4, max_length=200)

    @field_validator("name", "store_id")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(RefreshRequest):
    pass


class PasswordResetRequest(ApiModel):
    email: str = Field(min_length=3, max_length=255)


class PasswordResetConfirmRequest(ApiModel):
    reset_token: str = Field(min_length=32, max_length=500)
    new_password: str = Field(min_length=4, max_length=200)


class PasswordResetRequestResponse(ApiModel):
    message: str
    reset_token: str | None = None


class AuthUserResponse(ApiModel):
    id: str
    role: UserRole
    display_name: str
    store_id: str | None = None


class TokenResponse(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserResponse


class CustomerResponse(ApiModel):
    customer_id: str
    name: str
    membership: str
    visit_count: int
    preferred_colors: list[str]
    preferred_style: str
    recently_viewed_product_ids: list[str]
    liked_product_ids: list[str]
    purchase_count: int
    upcoming_schedule: str


class StoreResponse(ApiModel):
    store_id: str
    name: str
    timezone: str


class InventoryResponse(ApiModel):
    store_id: str
    quantity: int
    in_stock: bool
    updated_at: datetime


class ProductResponse(ApiModel):
    product_id: str
    name: str
    line: str
    category: str
    colors: list[str]
    material: str
    price: int
    tags: list[str]
    image_url: str
    inventory: InventoryResponse | None = None


class ProductListResponse(ApiModel):
    items: list[ProductResponse]
    next_cursor: str | None = None


class PurchaseResponse(ApiModel):
    purchase_id: str
    product_id: str
    name: str
    category: str
    price: int
    image_url: str
    purchased_at: datetime


class PurchaseListResponse(ApiModel):
    items: list[PurchaseResponse]
    next_cursor: str | None = None


class CheckinCreateRequest(ApiModel):
    tag_token: str = Field(min_length=8, max_length=255)


class EntryTagResponse(ApiModel):
    tag_token: str
    channel: EntryChannel
    store: StoreResponse
    checkin_url: str


class CheckinCreateResponse(ApiModel):
    checkin_id: str
    store: StoreResponse
    customer: dict[str, str]
    status: CheckinStatus
    checked_in_at: datetime
    purchase_count: int
    interest_count: int


class ShoppingModeRequest(ApiModel):
    shopping_mode: ShoppingMode


class ShoppingModeResponse(ApiModel):
    checkin_id: str
    shopping_mode: ShoppingMode
    status: CheckinStatus
    next_action: str


class ConsentRequest(ApiModel):
    agreed: bool
    policy_version: str = Field(min_length=1, max_length=80)
    scopes: list[str] = Field(min_length=1)


class VisitPurposeRequest(ApiModel):
    code: VisitPurposeCode
    note: str | None = Field(default=None, max_length=500)


class ServiceRequestCreate(ApiModel):
    consent: ConsentRequest
    visit_purpose: VisitPurposeRequest


class ServiceRequestResponse(ApiModel):
    checkin_id: str
    status: CheckinStatus
    ai_guide_status: str
    estimated_wait_minutes: int


class ConsentRevocationResponse(ApiModel):
    checkin_id: str
    consent_status: str
    shopping_mode: ShoppingMode
    checkin_status: CheckinStatus
    revoked_at: datetime


class StaffSummaryResponse(ApiModel):
    staff_id: str
    name: str
    title: str
    experience_years: int


class StaffAssignmentResponse(ApiModel):
    checkin_id: str
    status: CheckinStatus
    staff: StaffSummaryResponse
    assigned_at: datetime


class StaffVisitResponse(ApiModel):
    checkin_id: str
    customer_id: str
    masked_name: str
    membership: str
    visit_purpose: VisitPurposeCode
    waiting_since: datetime
    ai_guide_status: str


class StaffVisitListResponse(ApiModel):
    items: list[StaffVisitResponse]
    next_cursor: str | None = None


class StaffCustomerResponse(ApiModel):
    customer_id: str
    masked_name: str
    membership: str
    visit_count: int
    visit_purpose: VisitPurposeCode
    preferred_colors: list[str] | None = None
    preferred_style: str | None = None
    recently_viewed_product_ids: list[str] | None = None
    liked_product_ids: list[str] | None = None
    purchase_count: int | None = None


class StaffStatusRequest(ApiModel):
    status: CheckinStatus


class LookbookProductResponse(ApiModel):
    product_id: str
    product: str
    styling: str
    image_url: str
    price: int
    in_stock: bool


class LookbookResponse(ApiModel):
    title: str
    intro: str
    looks: list[LookbookProductResponse]
    closing: str
    generated_at: datetime


class GuideCustomerResponse(ApiModel):
    customer_id: str
    masked_name: str
    membership: str
    visit_count: int
    visit_purpose: VisitPurposeCode


class GuideProductResponse(ApiModel):
    product_id: str
    name: str
    reason: str
    image_url: str
    price: int
    quantity: int
    in_stock: bool


class StaffGuideResponse(ApiModel):
    checkin_id: str
    customer: GuideCustomerResponse
    customer_summary: str
    recommended_products: list[GuideProductResponse]
    greeting: str
    cross_sell: str
    caution: str
    generated_at: datetime


class CheckinResponse(ApiModel):
    checkin_id: str
    customer_id: str
    store_id: str
    shopping_mode: ShoppingMode | None
    visit_purpose_code: VisitPurposeCode | None
    visit_note: str | None
    status: CheckinStatus
    checked_in_at: datetime
    updated_at: datetime
    assigned_staff: StaffSummaryResponse | None = None


class MessageResponse(ApiModel):
    message: str
