from __future__ import annotations

from models.asset import Asset
from core.assets.assets import getMediaInfo


def resolveAsset(assetId: str, assetRegistry: dict[str, Asset]) -> Asset:
    asset = assetRegistry.get(assetId)
    if asset is None:
        raise ValueError(f"Asset not found: {assetId}")
    if asset.localPath is None:
        raise ValueError(f"Asset has no local path: {assetId}")
    return asset


def resolveAssetDuration(asset: Asset) -> float:
    info = getMediaInfo(asset)
    if info.duration is None:
        raise ValueError(f"Cannot determine duration for asset: {asset.id}")
    return info.duration


def buildAssetRegistry(assets: list[Asset]) -> dict[str, Asset]:
    return {a.id: a for a in assets}
