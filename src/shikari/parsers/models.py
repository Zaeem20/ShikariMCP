# ShikariMCP - normalized parser models

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Asset(BaseModel):
    value: str
    type: str = "host"
    source: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Service(BaseModel):
    host: str
    port: int
    protocol: str = "tcp"
    name: str = ""
    product: str = ""
    version: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Endpoint(BaseModel):
    url: str
    status_code: int | None = None
    title: str = ""
    technologies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    source: str
    value: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    title: str
    severity: str = "info"
    target: str = ""
    description: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedOutput(BaseModel):
    assets: list[Asset] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    endpoints: list[Endpoint] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    def to_runner_fields(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "assets": [item.model_dump() for item in self.assets],
            "services": [item.model_dump() for item in self.services],
            "endpoints": [item.model_dump() for item in self.endpoints],
            "findings": [item.model_dump() for item in self.findings],
        }
