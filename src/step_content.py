import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Final

from content_types import (
    AI_SECTION_TYPES,
    AiSectionType,
    DEVELOPMENT_MARKER,
    LEVELS,
    SECTION_TYPES,
    STYLE_ORDER,
    Block,
    Content,
    ContentError,
    Level,
    ProfileText,
    Question,
    Section,
    Source,
    SourcedText,
    StyleDef,
    StyleKey,
)

logger = logging.getLogger(__name__)

QUESTION_COUNT: Final[int] = 30
EXPECTED_SECTION_COUNTS: Final[Counter[str]] = Counter(
    {"davranis": 1, "uygun": 1, "uygun_degil": 1, "siz_iseniz": 1, "karsi_taraf": 1}
)
# Kartlar kısa ve taranabilir kalsın diye her bölümde en fazla bu kadar madde olur.
MAX_SECTION_ITEMS: Final[int] = 4

class ContentStep:
    """src/content altındaki içerik dosyalarını yükler ve doğrular."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def load(self) -> Content:
        questions = self._load_questions()
        styles, answer_key = self._load_scoring()
        sunum = {style: self._load_sunum(style) for style in STYLE_ORDER}
        sources = self._load_sources()
        source_ids = {source.id for source in sources}
        blocks = self._load_blocks(source_ids)
        ai_bolumler = self._load_ai_sections(source_ids)
        profiles = self._load_profiles(source_ids)
        logger.info(
            "İçerik yüklendi: %d soru, %d kaynak, %d blok, %d profil",
            len(questions),
            len(sources),
            len(blocks),
            len(profiles),
        )
        return Content(
            questions=questions,
            styles=styles,
            answer_key=answer_key,
            sunum=sunum,
            sources=sources,
            blocks=blocks,
            ai_bolumler=ai_bolumler,
            profiles=profiles,
        )

    def _read_json(self, relative: str) -> Any:
        path = self._root / relative
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ContentError(f"{relative} okunamadı: {exc}") from exc

    def _load_questions(self) -> list[Question]:
        raw = self._read_json("questions.json")
        if not isinstance(raw, list):
            raise ContentError("questions.json bir liste olmalı")
        try:
            questions = [Question(no=int(item["no"]), a=str(item["a"]), b=str(item["b"])) for item in raw]
        except (KeyError, TypeError, ValueError) as exc:
            raise ContentError(f"questions.json hatalı kayıt içeriyor: {exc}") from exc
        numbers = [question.no for question in questions]
        if sorted(numbers) != list(range(1, QUESTION_COUNT + 1)):
            raise ContentError(f"questions.json 1-{QUESTION_COUNT} arası soruları eksiksiz içermeli")
        if any(not question.a.strip() or not question.b.strip() for question in questions):
            raise ContentError("questions.json içinde boş şık var")
        return sorted(questions, key=lambda question: question.no)

    def _load_scoring(self) -> tuple[list[StyleDef], dict[int, dict[str, str]]]:
        raw = self._read_json("scoring.json")
        try:
            styles = [
                StyleDef(
                    key=item["key"],
                    name=str(item["name"]),
                    high=int(item["high"]),
                    low=int(item["low"]),
                    x=int(item["x"]),
                    y=int(item["y"]),
                )
                for item in raw["styles"]
            ]
            raw_key = raw["key"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ContentError(f"scoring.json hatalı: {exc}") from exc

        if [style.key for style in styles] != list(STYLE_ORDER):
            raise ContentError(f"scoring.json tarzları şu sırada olmalı: {', '.join(STYLE_ORDER)}")
        for style in styles:
            if not style.low < style.high:
                raise ContentError(f"scoring.json {style.key}: düşük eşik yüksek eşikten küçük olmalı")

        answer_key: dict[int, dict[str, str]] = {}
        for number in range(1, QUESTION_COUNT + 1):
            options = raw_key.get(str(number))
            if not isinstance(options, dict) or set(options) != {"A", "B"}:
                raise ContentError(f"scoring.json anahtarında {number}. soru için A ve B olmalı")
            for letter, style_key in options.items():
                if style_key not in STYLE_ORDER:
                    raise ContentError(f"scoring.json {number}{letter}: bilinmeyen tarz '{style_key}'")
            answer_key[number] = dict(options)
        return styles, answer_key

    def _load_sunum(self, style: StyleKey) -> list[Section]:
        relative = f"sunum/{style}.json"
        raw = self._read_json(relative)
        try:
            sections = [
                Section(tur=item["tur"], baslik=str(item["baslik"]), maddeler=[str(m) for m in item["maddeler"]])
                for item in raw["bolumler"]
            ]
        except (KeyError, TypeError) as exc:
            raise ContentError(f"{relative} hatalı: {exc}") from exc

        for section in sections:
            if section.tur not in SECTION_TYPES:
                raise ContentError(f"{relative}: bilinmeyen bölüm türü '{section.tur}'")
            if not section.maddeler:
                raise ContentError(f"{relative}: '{section.baslik}' bölümünde madde yok")
            if len(section.maddeler) > MAX_SECTION_ITEMS:
                raise ContentError(f"{relative}: '{section.baslik}' bölümünde en fazla {MAX_SECTION_ITEMS} madde olmalı")

        counts = Counter(section.tur for section in sections)
        if counts != EXPECTED_SECTION_COUNTS:
            raise ContentError(
                f"{relative}: bölüm türleri {dict(EXPECTED_SECTION_COUNTS)} olmalı, {dict(counts)} bulundu"
            )
        return sections

    def _load_sources(self) -> list[Source]:
        relative = "kaynakli/kaynaklar.json"
        raw = self._read_json(relative)
        try:
            sources = [Source(id=str(i["id"]), kaynakca=str(i["kaynakca"]), ozet=str(i["ozet"])) for i in raw]
        except (KeyError, TypeError) as exc:
            raise ContentError(f"{relative} hatalı: {exc}") from exc
        ids = [source.id for source in sources]
        if not sources or len(ids) != len(set(ids)):
            raise ContentError(f"{relative}: kaynak listesi boş ya da tekrar eden kimlik var")
        return sources

    def _load_blocks(self, source_ids: set[str]) -> dict[tuple[StyleKey, Level], Block]:
        relative = "kaynakli/bloklar.json"
        raw = self._read_json(relative)
        blocks: dict[tuple[StyleKey, Level], Block] = {}
        for style in STYLE_ORDER:
            for level in LEVELS:
                try:
                    item = raw[style][level]
                    block = Block(metin=str(item["metin"]), kaynaklar=[str(k) for k in item["kaynaklar"]])
                except (KeyError, TypeError) as exc:
                    raise ContentError(f"{relative}: {style}/{level} eksik ya da hatalı") from exc
                self._check_text(relative, f"{style}/{level}", block.metin, block.kaynaklar, source_ids)
                if block.metin.count(DEVELOPMENT_MARKER) != 1:
                    raise ContentError(f"{relative}: {style}/{level} tam bir 'Gelişim için' paragrafı içermeli")
                blocks[(style, level)] = block
        return blocks

    def _load_ai_sections(self, source_ids: set[str]) -> dict[StyleKey, dict[AiSectionType, SourcedText]]:
        relative = "kaynakli/bolumler.json"
        raw = self._read_json(relative)
        sections: dict[StyleKey, dict[AiSectionType, SourcedText]] = {}
        for style in STYLE_ORDER:
            sections[style] = {}
            for tur in AI_SECTION_TYPES:
                try:
                    item = raw[style][tur]
                    text = SourcedText(metin=str(item["metin"]), kaynaklar=[str(k) for k in item["kaynaklar"]])
                except (KeyError, TypeError) as exc:
                    raise ContentError(f"{relative}: {style}/{tur} eksik ya da hatalı") from exc
                self._check_text(relative, f"{style}/{tur}", text.metin, text.kaynaklar, source_ids)
                sections[style][tur] = text
        return sections

    def _load_profiles(self, source_ids: set[str]) -> dict[tuple[StyleKey, StyleKey], ProfileText]:
        relative = "kaynakli/profiller.json"
        raw = self._read_json(relative)
        profiles: dict[tuple[StyleKey, StyleKey], ProfileText] = {}
        for dominant in STYLE_ORDER:
            for least in STYLE_ORDER:
                if dominant == least:
                    continue
                name = f"{dominant}__{least}"
                try:
                    item = raw[name]
                    profile = ProfileText(
                        baslik=str(item["baslik"]),
                        giris=str(item["giris"]),
                        guclu=str(item["guclu"]),
                        zayif=str(item["zayif"]),
                        oneri=str(item["oneri"]),
                        kaynaklar=[str(k) for k in item["kaynaklar"]],
                    )
                except (KeyError, TypeError) as exc:
                    raise ContentError(f"{relative}: {name} eksik ya da hatalı") from exc
                for part in (profile.giris, profile.guclu, profile.zayif, profile.oneri):
                    self._check_text(relative, name, part, profile.kaynaklar, source_ids)
                profiles[(dominant, least)] = profile
        return profiles

    @staticmethod
    def _check_text(relative: str, name: str, text: str, refs: list[str], source_ids: set[str]) -> None:
        if not text.strip():
            raise ContentError(f"{relative}: {name} metni boş")
        if not refs:
            raise ContentError(f"{relative}: {name} en az bir kaynağa dayanmalı")
        unknown = [ref for ref in refs if ref not in source_ids]
        if unknown:
            raise ContentError(f"{relative}: {name} tanımsız kaynak kullanıyor: {', '.join(unknown)}")
