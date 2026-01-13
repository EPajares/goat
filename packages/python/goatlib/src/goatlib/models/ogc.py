"""Shared OGC API models.

Base models used across OGC API Features, Tiles, and Processes services.
"""

from pydantic import BaseModel, Field


class Link(BaseModel):
    """OGC API Link model.

    Common link structure used across all OGC APIs.
    Ref: https://docs.ogc.org/is/17-069r4/17-069r4.html#_link
    """

    href: str
    rel: str
    type: str | None = None
    title: str | None = None
    hreflang: str | None = None
    length: int | None = None
    templated: bool | None = None


class LandingPage(BaseModel):
    """OGC API Landing Page.

    Common landing page structure for OGC API services.
    Ref: https://docs.ogc.org/is/17-069r4/17-069r4.html#_api_landing_page
    """

    title: str
    description: str | None = None
    links: list[Link] = Field(default_factory=list)


class ConformanceDeclaration(BaseModel):
    """OGC API Conformance Declaration.

    Declares which conformance classes the API implements.
    Ref: https://docs.ogc.org/is/17-069r4/17-069r4.html#_declaration_of_conformance_classes
    """

    conformsTo: list[str] = Field(default_factory=list)  # noqa: N815 - OGC spec uses camelCase
