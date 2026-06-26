from __future__ import annotations

import json

from shikari.parsers.models import Asset, Finding, ParsedOutput


def _extract_gps(obj: dict) -> tuple[float | None, float | None]:
    lat = obj.get("GPS:GPSLatitude") or obj.get("GPSLatitude")
    lon = obj.get("GPS:GPSLongitude") or obj.get("GPSLongitude")
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (ValueError, TypeError):
            pass

    pos = obj.get("GPS:GPSPosition") or obj.get("GPSPosition")
    if pos and isinstance(pos, str) and "," in pos:
        parts = pos.split(",")
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except (ValueError, TypeError):
            pass

    return None, None


def _summarize_tags(obj: dict) -> str:
    """Build a short summary from key EXIF tags."""
    parts = []
    make = obj.get("EXIF:Make") or obj.get("Make")
    model = obj.get("EXIF:Model") or obj.get("Model")
    if make:
        parts.append(f"Make={make}")
    if model:
        parts.append(f"Model={model}")
    datetime = (
        obj.get("EXIF:DateTimeOriginal")
        or obj.get("DateTimeOriginal")
        or obj.get("XMP:DateTimeOriginal")
    )
    if datetime:
        parts.append(f"Date={datetime}")
    parts.append(f"File={obj.get('SourceFile', '')}")
    return "; ".join(parts)


def parse_json(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return parsed

    if not isinstance(data, list):
        data = [data]

    for obj in data:
        if not isinstance(obj, dict):
            continue

        source_file = (obj.get("SourceFile") or "").strip()
        if not source_file:
            continue

        summary = _summarize_tags(obj)
        parsed.findings.append(
            Finding(
                title=f"Metadata for {source_file}",
                severity="info",
                target=source_file,
                description=summary,
                metadata=obj,
            )
        )

        lat, lon = _extract_gps(obj)
        if lat is not None and lon is not None:
            parsed.assets.append(
                Asset(
                    value=f"{lat},{lon}",
                    type="geolocation",
                    source="exiftool",
                    metadata={"latitude": lat, "longitude": lon},
                )
            )

    return parsed


def parse_gps(raw: str) -> ParsedOutput:
    parsed = ParsedOutput()
    if not raw.strip():
        return parsed

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return parsed

    if not isinstance(data, list):
        data = [data]

    for obj in data:
        if not isinstance(obj, dict):
            continue

        source_file = (obj.get("SourceFile") or "").strip()
        if not source_file:
            continue

        lat, lon = _extract_gps(obj)
        if lat is not None and lon is not None:
            parsed.assets.append(
                Asset(
                    value=f"{lat},{lon}",
                    type="geolocation",
                    source="exiftool",
                )
            )
            parsed.findings.append(
                Finding(
                    title="GPS coordinates extracted",
                    severity="info",
                    description=f"File {source_file} contains GPS coordinates: {lat}, {lon}",
                )
            )

    return parsed
