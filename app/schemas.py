"""Version-one request contracts for externally reachable API boundaries."""
from decimal import Decimal
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    """Registration data accepted by the first-party dashboard."""
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12, max_length=256)
    phone: str = Field(default="", max_length=40)


class LoginRequest(BaseModel):
    """Credentials for an existing local account during the OIDC transition."""
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AdminLoginRequest(BaseModel):
    """Environment-managed administrator password submission."""
    password: str = Field(min_length=1, max_length=256)


class GitHubDeployRequest(BaseModel):
    """Bounded inputs for the legacy, disabled GitHub deployment adapter."""
    model_config = ConfigDict(extra="forbid")

    github_token: str = Field(default="", max_length=256)
    repo_name: str = Field(default="", max_length=100)
    is_private: bool = Field(default=False, strict=True)


class VercelDeployRequest(BaseModel):
    """Bounded inputs for Vercel deployment without arbitrary outbound URLs."""
    model_config = ConfigDict(extra="forbid")

    deploy_hook: str = Field(default="", max_length=512)
    vercel_token: str = Field(default="", max_length=256)
    project_name: str = Field(default="", max_length=100)

    @field_validator("deploy_hook")
    @classmethod
    def validate_deploy_hook(cls, value: str) -> str:
        """Only accept the documented Vercel hook endpoint, never arbitrary hosts."""
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Deploy hooks must be valid Vercel HTTPS URLs") from exc
        valid_path = re.fullmatch(
            r"/v1/integrations/deploy/prj_[A-Za-z0-9]+/[A-Za-z0-9_-]+",
            parsed.path,
        )
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.vercel.com"
            or port not in (None, 443)
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not valid_path
        ):
            raise ValueError("Deploy hooks must use Vercel's HTTPS integration endpoint")
        return value


class SiteFileSaveRequest(BaseModel):
    """Bounded content contract for the disabled prototype file editor."""
    model_config = ConfigDict(extra="forbid")

    content: str = Field(max_length=1_000_000)


class JobDecisionRequest(BaseModel):
    """Require an explicit, supported workflow decision from an administrator."""
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]


class SiteAutomationDecisionRequest(BaseModel):
    """Require a pending campaign ID and explicit owner decision."""
    model_config = ConfigDict(extra="forbid")

    automation_id: int = Field(ge=1, strict=True)
    decision: Literal["approve", "reject"]


class SiteSettingsPatchRequest(BaseModel):
    """Allow bounded partial updates to public storefront settings."""
    model_config = ConfigDict(extra="forbid")

    brand_name: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    custom_domain: str | None = Field(default=None, max_length=253)
    color_primary: str | None = Field(default=None, max_length=16)
    color_secondary: str | None = Field(default=None, max_length=16)
    logo_url: str | None = Field(default=None, max_length=512)
    phone: str | None = Field(default=None, max_length=40)
    whatsapp: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    vodafone_cash: str | None = Field(default=None, max_length=128)
    instapay: str | None = Field(default=None, max_length=128)
    fawry_code: str | None = Field(default=None, max_length=128)
    cod_enabled: bool | None = Field(default=None, strict=True)

    @field_validator("custom_domain")
    @classmethod
    def validate_custom_domain(cls, value: str | None) -> str | None:
        """Accept a hostname only; domain verification remains a separate workflow."""
        if value is None or not value.strip():
            return ""
        try:
            # Keep internationalized merchant domains usable after DNS IDNA encoding.
            domain = value.strip().rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("Custom domain must be a valid hostname") from exc
        labels = domain.split(".")
        if (
            len(domain) > 253
            or len(labels) < 2
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in labels
            )
        ):
            raise ValueError("Custom domain must be a valid hostname")
        return domain

    @field_validator("color_primary", "color_secondary")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?(?:[0-9A-Fa-f]{2})?", value):
            raise ValueError("Color must be a hexadecimal CSS color")
        return value


    @field_validator("logo_url")
    @classmethod
    def validate_logo_url(cls, value: str | None) -> str | None:
        """Keep storefront logos HTTPS-only or on the sanitized upload path."""
        if value is None or value == "":
            return value
        if re.fullmatch(r"/static/uploads/[A-Za-z0-9_-]{1,80}\.(?:jpe?g|png|webp)", value, re.I):
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Logo URL must be HTTPS or a sanitized local upload") from exc
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or port not in (None, 443)
        ):
            raise ValueError("Logo URL must be HTTPS or a sanitized local upload")
        return value


class PostDecisionRequest(BaseModel):
    """Require an explicit administrator decision before a post is published or dropped."""
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]


class ProposalDecisionRequest(BaseModel):
    """Allow only explicit proposal approval, rejection, or prompt rollback."""
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject", "rollback"]


class SiteRefineRequest(BaseModel):
    """Bound untrusted refinement instructions and attached context before LLM use."""
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1, max_length=4000)
    extracted_text: str = Field(default="", max_length=50_000)
    file_url: str = Field(default="", max_length=512)

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, value: str) -> str:
        if not value:
            return value
        if re.fullmatch(r"/static/uploads/[A-Za-z0-9_-]{1,80}\.(?:jpe?g|png|webp)", value, re.I):
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Attached file URL must be HTTPS or a sanitized local upload") from exc
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or port not in (None, 443)
        ):
            raise ValueError("Attached file URL must be HTTPS or a sanitized local upload")
        return value


class MarketingEmailDraftRequest(BaseModel):
    """Bound merchant-provided context used to draft an email campaign."""
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(default="", max_length=500)
    target_audience: str = Field(default="", max_length=300)


class SocialPostDraftRequest(BaseModel):
    """Constrain platform text interpolated into the marketing system prompt."""
    model_config = ConfigDict(extra="forbid")

    platform: Literal["facebook", "instagram", "tiktok", "linkedin", "x"] = "facebook"
    theme: str = Field(default="", max_length=500)


class VisualSiteEditRequest(BaseModel):
    """Bound fields accepted by the first-party visual storefront editor."""
    model_config = ConfigDict(extra="forbid")

    brand_name: str | None = Field(default=None, max_length=120)
    slogan: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=80)
    color_primary: str | None = Field(default=None, max_length=16)
    color_secondary: str | None = Field(default=None, max_length=16)
    logo_url: str | None = Field(default=None, max_length=512)
    phone: str | None = Field(default=None, max_length=40)
    whatsapp: str | None = Field(default=None, max_length=40)
    vodafone_cash: str | None = Field(default=None, max_length=128)
    instapay: str | None = Field(default=None, max_length=128)
    theme: Literal["dark", "light"] = "dark"
    enable_faq: bool | None = Field(default=None, strict=True)
    enable_testimonials: bool | None = Field(default=None, strict=True)
    enable_gallery: bool | None = Field(default=None, strict=True)
    enable_reviews: bool | None = Field(default=None, strict=True)
    enable_promo: bool | None = Field(default=None, strict=True)

    @field_validator("color_primary", "color_secondary")
    @classmethod
    def validate_visual_color(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?(?:[0-9A-Fa-f]{2})?", value):
            raise ValueError("Color must be a hexadecimal CSS color")
        return value

    @field_validator("logo_url")
    @classmethod
    def validate_visual_logo(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if re.fullmatch(r"/static/uploads/[A-Za-z0-9_-]{1,80}\.(?:jpe?g|png|webp)", value, re.I):
            return value
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Logo URL must be HTTPS or a sanitized local upload") from exc
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or port not in (None, 443)
        ):
            raise ValueError("Logo URL must be HTTPS or a sanitized local upload")
        return value


class ProjectCatalogItemRequest(BaseModel):
    """A bounded catalog item supplied with a new project brief."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    price: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("1000000000"))
    category: str = Field(default="", max_length=80)
    badge: str = Field(default="", max_length=40)


class ProjectAnswerRequest(BaseModel):
    """One bounded response from the project discovery wizard."""
    model_config = ConfigDict(extra="forbid")

    label: str = Field(default="", max_length=120)
    a: str = Field(min_length=1, max_length=500)


class ProjectFeaturesRequest(BaseModel):
    """Supported feature toggles accepted by the first-party wizard."""
    model_config = ConfigDict(extra="forbid")

    auth: bool = True
    bilingual: bool = True
    darklight: bool = True
    reviews: bool = True
    promos: bool = True
    admin: bool = True
    docker: bool = True
    hostinger: bool = True


class ProjectCreateRequest(BaseModel):
    """Bounded project wizard contract; the server controls execution mode."""
    model_config = ConfigDict(extra="forbid")

    request: str = Field(default="", max_length=4000)
    brand_name: str = Field(default="", max_length=120)
    client: str = Field(default="", max_length=120)
    category: str = Field(default="", max_length=80)
    slogan: str = Field(default="", max_length=500)
    extracted_text: str = Field(default="", max_length=1_000_000)
    ai_answers: list[ProjectAnswerRequest] = Field(default_factory=list, max_length=20)
    items: list[ProjectCatalogItemRequest] = Field(default_factory=list, max_length=50)
    features: ProjectFeaturesRequest = Field(default_factory=ProjectFeaturesRequest)
    custom_domain: str = Field(default="", max_length=253)
    color_primary: str = Field(default="", max_length=16)
    color_secondary: str = Field(default="", max_length=16)
    palette: str = Field(default="", max_length=80)
    logo_url: str = Field(default="", max_length=512)
    phone: str = Field(default="", max_length=40)
    whatsapp: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=500)
    vodafone_cash: str = Field(default="", max_length=128)
    instapay: str = Field(default="", max_length=128)
    fawry_code: str = Field(default="", max_length=128)
    cod_enabled: bool = True


class SiteItemCreateRequest(BaseModel):
    """Bounded merchant catalog fields accepted when creating a product."""
    title: str = Field(min_length=1, max_length=160)
    price: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("1000000000"), max_digits=12, decimal_places=2)
    category: str = Field(default="عام", max_length=80)
    description: str = Field(default="", max_length=2000)
    badge: str = Field(default="", max_length=40)
    image_url: str = Field(default="", max_length=512)


class SiteOrderItemRequest(BaseModel):
    """One bounded customer-supplied line; price is informational only."""
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=200)
    price: Decimal | None = Field(default=None, ge=0, le=Decimal("1000000000"))
    quantity: int = Field(ge=1, le=50, strict=True)

    @field_validator("id", mode="before")
    @classmethod
    def parse_catalog_id(cls, value):
        """Accept numeric storefront IDs without treating booleans as IDs."""
        if value is None:
            return None
        if isinstance(value, bool) or not (
            isinstance(value, int)
            or (isinstance(value, str) and value.isascii() and value.isdecimal())
        ):
            raise ValueError("Catalog item ID must be a positive integer")
        return int(value)


class SiteOrderCreateRequest(BaseModel):
    """Bounded public order request; server catalog data remains authoritative."""
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(min_length=2, max_length=100)
    customer_phone: str = Field(min_length=6, max_length=30)
    customer_address: str = Field(default="", max_length=200)
    payment_method: str = Field(default="cash", min_length=1, max_length=30)
    total_egp: Decimal | None = Field(default=None, ge=0, le=Decimal("1000000000"))
    items: list[SiteOrderItemRequest] = Field(min_length=1, max_length=20)
