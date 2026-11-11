from content_types import Section
from presentation import sunum_view
from scoring import StyleResult

SECTIONS = [
    Section(tur="davranis", baslik="D", maddeler=["d"]),
    Section(tur="uygun", baslik="U1", maddeler=["u1"]),
    Section(tur="uygun", baslik="U2", maddeler=["u2"]),
    Section(tur="siz_iseniz", baslik="S", maddeler=["s"]),
    Section(tur="karsi_taraf", baslik="K", maddeler=["k"]),
]


def _result(level: str) -> StyleResult:
    return StyleResult(style="kacinma", score=5, level=level, relative=0.25)


def test_sunum_view_high_puts_siz_iseniz_first() -> None:
    view = sunum_view(_result("yuksek"), SECTIONS)

    assert view.acik is True
    assert view.not_metni is None
    assert [s.baslik for s in view.bolumler] == ["S", "D", "U1", "U2", "K"]


def test_sunum_view_low_shows_only_uygun() -> None:
    view = sunum_view(_result("dusuk"), SECTIONS)

    assert view.acik is True
    assert view.not_metni == "Bu tarzı az kullanıyorsunuz. Şu durumlarda işe yarayabilir:"
    assert [s.baslik for s in view.bolumler] == ["U1", "U2"]


def test_sunum_view_mid_collapsed() -> None:
    view = sunum_view(_result("orta"), SECTIONS)

    assert view.acik is False
    assert view.not_metni is None
    assert [s.baslik for s in view.bolumler] == ["D", "U1", "U2", "S", "K"]
