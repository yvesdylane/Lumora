from __future__ import annotations

from models.renderParams import TextParams

FONT_FILES: dict[str, str] = {
    "Inter": "/usr/share/fonts/rsms-inter-fonts/Inter-Regular.ttf",
    "Montserrat": "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Regular.otf",
    "Source Code Pro": "/usr/share/fonts/adobe-source-code-pro-fonts/SourceCodePro-Regular.otf",
    "Open Sans": "/usr/share/fonts/open-sans/OpenSans-Regular.ttf",
    "Liberation Sans": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
    "Liberation Serif": "/usr/share/fonts/liberation-serif-fonts/LiberationSerif-Regular.ttf",
    "DejaVu Sans": "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "Arial": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
}

DEFAULT_FONT_FILE = FONT_FILES["Liberation Sans"]


def resolveFontFile(params: TextParams) -> str:
    name = params.fontFamily or params.font or "Arial"
    return FONT_FILES.get(name, DEFAULT_FONT_FILE)
