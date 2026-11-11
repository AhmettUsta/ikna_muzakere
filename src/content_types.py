from dataclasses import dataclass, field
from typing import Final, Literal

StyleKey = Literal["rekabet", "isbirligi", "uzlasma", "kacinma", "iltifat"]
STYLE_ORDER: Final[tuple[StyleKey, ...]] = (
    "rekabet",
    "isbirligi",
    "uzlasma",
    "kacinma",
    "iltifat",
)

Level = Literal["yuksek", "orta", "dusuk"]
LEVELS: Final[tuple[Level, ...]] = ("yuksek", "orta", "dusuk")


SectionType = Literal["davranis", "uygun", "uygun_degil", "siz_iseniz", "karsi_taraf"]
SECTION_TYPES: Final[tuple[SectionType, ...]] = (
    "davranis",
    "uygun",
    "uygun_degil",
    "siz_iseniz",
    "karsi_taraf",
)


class ContentError(ValueError):
    """İçerik dosyaları eksik ya da tutarsız olduğunda fırlatılır."""


@dataclass(frozen=True)
class Question:
    no: int
    a: str
    b: str


@dataclass(frozen=True)
class StyleDef:
    key: StyleKey
    name: str
    high: int
    low: int
    x: int
    y: int


@dataclass(frozen=True)
class Section:
    tur: SectionType
    baslik: str
    maddeler: list[str]


@dataclass(frozen=True)
class Source:
    id: str
    kaynakca: str
    ozet: str


DEVELOPMENT_MARKER: Final[str] = "\n\n**Gelişim için:**"


@dataclass(frozen=True)
class Block:
    metin: str
    kaynaklar: list[str]

    @property
    def aciklama(self) -> str:
        """Bloğun 'Gelişim için' paragrafından önceki akademik açıklama kısmı."""
        return self.metin.split(DEVELOPMENT_MARKER, 1)[0].strip()

    @property
    def gelisim(self) -> str:
        """Bloğun 'Gelişim için' paragrafı, başlık olmadan."""
        parts = self.metin.split(DEVELOPMENT_MARKER, 1)
        return parts[1].strip() if len(parts) == 2 else ""


@dataclass(frozen=True)
class ProfileText:
    baslik: str
    metin: str
    kaynaklar: list[str]


@dataclass
class Content:
    questions: list[Question]
    styles: list[StyleDef]
    answer_key: dict[int, dict[str, StyleKey]]
    sunum: dict[StyleKey, list[Section]]
    sources: list[Source]
    blocks: dict[tuple[StyleKey, Level], Block]
    profiles: dict[tuple[StyleKey, StyleKey], ProfileText]
    style_by_key: dict[StyleKey, StyleDef] = field(init=False)

    def __post_init__(self) -> None:
        self.style_by_key = {style.key: style for style in self.styles}
