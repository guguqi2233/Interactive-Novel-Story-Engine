from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PROVIDER_GATEWAY_V2_CONTRACT = "2"


class ProviderError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ProviderGatewayV2Config(BaseModel):
    provider_id: str = "local_stub"
    provider_type: Literal["mock", "local_stub", "local_http", "openai"] = "mock"
    contract_version: str = PROVIDER_GATEWAY_V2_CONTRACT
    model_id: str = "mock-model"
    capabilities: list[str] = Field(default_factory=lambda: ["generate_text", "generate_json"])
    env_var_refs: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "contract_version": self.contract_version,
            "model_id": self.model_id,
            "capabilities": self.capabilities,
            "configured": True,
        }


class ProviderRoutingCompatibilityReport(BaseModel):
    ok: bool
    provider_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def validate_provider_gateway_v2(config: ProviderGatewayV2Config) -> ProviderRoutingCompatibilityReport:
    if config.contract_version != PROVIDER_GATEWAY_V2_CONTRACT:
        return ProviderRoutingCompatibilityReport(ok=False, provider_id=config.provider_id, errors=["Unsupported provider gateway contract_version"])
    return ProviderRoutingCompatibilityReport(ok=True, provider_id=config.provider_id)
