from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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


class LoginRequest(ApiModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=200)


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(RefreshRequest):
    pass


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


class CheckinCreateRequest(ApiModel):
    tag_token: str = Field(min_length=8, max_length=255)


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
