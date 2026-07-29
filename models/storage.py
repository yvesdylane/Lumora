from __future__ import annotations

from enum import Enum


class StoragePrefix(str, Enum):
    UPLOADS = "uploads"
    STAGING = "staging"
    GENERATED_AUDIO = "generated-audio"
    GENERATED_IMAGE = "generated-image"
    RENDERS = "renders"
    MANIFESTS = "manifests"

    def __str__(self) -> str:
        return self.value
