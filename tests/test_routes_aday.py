from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from conftest import DESIGN_EXAMPLE, OWNER_ID, PUBLIC_ID
from main import create_app
from step_database import DatabaseUnavailable
from step_gemini import LiveCommentUnavailable


def client_for(service) -> TestClient:
    return TestClient(create_app(service, session_secret="test-secret", cookie_secure=False))


def registered_client(service) -> TestClient:
    client = client_for(service)
    response = client.post(
        "/kayit", data={"nickname": "Ali", "pin": "1234", "pin_again": "1234"}, follow_redirects=False
    )
    assert response.status_code == 303
    return client


def answers_form(answers: str) -> dict[str, str]:
    return {f"q{i + 1}": letter for i, letter in enumerate(answers)}


def test_robots_and_noindex(make_web_service) -> None:
    client = client_for(make_web_service())

    robots = client.get("/robots.txt")
    home = client.get("/")

    assert robots.status_code == 200 and "Disallow: /" in robots.text
    assert home.status_code == 200
    assert '<meta name="robots" content="noindex, nofollow">' in home.text


def test_health(make_web_service) -> None:
    assert client_for(make_web_service()).get("/saglik").text == "ok"


def test_register_then_redirect_test(make_web_service) -> None:
    client = client_for(make_web_service())

    response = client.post(
        "/kayit", data={"nickname": "Ali", "pin": "1234", "pin_again": "1234"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/test"
    assert "Soru 1" in client.get("/test").text


def test_register_error_shows_message(make_web_service) -> None:
    response = client_for(make_web_service()).post(
        "/kayit", data={"nickname": "Ali", "pin": "1234", "pin_again": "9999"}
    )

    assert response.status_code == 400
    assert "PIN&#39;ler birbiriyle aynı değil." in response.text


def test_test_requires_session(make_web_service) -> None:
    response = client_for(make_web_service()).get("/test", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_submit_complete_redirects_to_result(make_web_service, fake_db) -> None:
    client = registered_client(make_web_service())

    response = client.post("/test", data=answers_form(DESIGN_EXAMPLE), follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"/sonuc/{PUBLIC_ID}"
    fake_db.create_attempt.assert_called_once()


@pytest.mark.parametrize(
    "form",
    [
        answers_form(DESIGN_EXAMPLE[:29]),
        {**answers_form(DESIGN_EXAMPLE), "q5": "C"},
        {},
        {k: v for k, v in {**answers_form(DESIGN_EXAMPLE), "q1": "AB"}.items() if k != "q2"},
    ],
)
def test_submit_incomplete_shows_message(make_web_service, fake_db, form) -> None:
    client = registered_client(make_web_service())

    response = client.post("/test", data=form)

    assert response.status_code == 400
    assert "Lütfen 30 sorunun hepsini cevaplayın." in response.text
    fake_db.create_attempt.assert_not_called()


def test_result_owner_sees_scores_and_chart(make_web_service) -> None:
    client = registered_client(make_web_service())

    page = client.get(f"/sonuc/{PUBLIC_ID}")

    assert page.status_code == 200
    assert "<svg" in page.text and "Rekabetçi · 9" in page.text
    assert "kişilik testi değildir" in page.text
    assert "Sunum yorumları" in page.text and "Kaynaklarla genişletilmiş yorum" in page.text


def test_result_other_user_404(make_web_service, fake_db) -> None:
    fake_db.create_participant.return_value = OWNER_ID + 1
    client = registered_client(make_web_service())

    assert client.get(f"/sonuc/{PUBLIC_ID}").status_code == 404


def test_result_without_session_404(make_web_service) -> None:
    assert client_for(make_web_service()).get(f"/sonuc/{PUBLIC_ID}").status_code == 404


def test_result_invalid_id_404(make_web_service) -> None:
    client = registered_client(make_web_service())

    assert client.get("/sonuc/abc").status_code == 404


def test_personalize_box_disabled_when_live_off(make_web_service) -> None:
    client = registered_client(make_web_service())

    page = client.get(f"/sonuc/{PUBLIC_ID}").text

    assert "canli-yorum" not in page
    assert 'id="kisisellestir" disabled' in page
    assert page.index("Kaynaklarla genişletilmiş yorum") < page.index('id="kisisellestir"')


def test_personalize_box_active_when_live_on(make_web_service) -> None:
    client = registered_client(make_web_service(gemini=MagicMock()))

    page = client.get(f"/sonuc/{PUBLIC_ID}").text

    assert "canli-yorum" in page
    assert 'id="kisisellestir" disabled' not in page


def test_live_comment_success_redirects(make_web_service, fake_db) -> None:
    gemini = MagicMock()
    gemini.generate.return_value = "Canlı"
    client = registered_client(make_web_service(gemini=gemini))

    response = client.post(f"/sonuc/{PUBLIC_ID}/canli-yorum", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/sonuc/{PUBLIC_ID}")
    fake_db.save_ai_comment.assert_called_once()


def test_live_unavailable_message(make_web_service) -> None:
    gemini = MagicMock()
    gemini.generate.side_effect = LiveCommentUnavailable("kota")
    client = registered_client(make_web_service(gemini=gemini))

    page = client.post(f"/sonuc/{PUBLIC_ID}/canli-yorum")

    assert page.status_code == 200
    assert "Şu anda canlı yorum üretilemiyor, daha sonra tekrar deneyin." in page.text


def test_db_unavailable_503(make_web_service, fake_db) -> None:
    fake_db.get_attempt.side_effect = DatabaseUnavailable("down")
    client = registered_client(make_web_service())

    page = client.get(f"/sonuc/{PUBLIC_ID}")

    assert page.status_code == 503
    assert "Şu anda hizmet veremiyoruz" in page.text


def test_history_requires_session(make_web_service) -> None:
    response = client_for(make_web_service()).get("/gecmis", follow_redirects=False)

    assert response.status_code == 303


def test_login_then_history(make_web_service, fake_db) -> None:
    from security import PinHasher
    from step_database import ParticipantRow

    digest, salt = PinHasher().hash("1234")
    fake_db.reserve_login_attempt.return_value = ParticipantRow(
        id=OWNER_ID, nickname="Ali", pin_hash=digest, pin_salt=salt, failed_pins=0, locked_until=None
    )
    client = client_for(make_web_service())

    response = client.post("/giris", data={"nickname": "ali", "pin": "1234"}, follow_redirects=False)
    history = client.get("/gecmis")

    assert response.headers["location"] == "/gecmis"
    assert "Testi tekrar çöz" in history.text
    assert f"/sonuc/{PUBLIC_ID}" in history.text


def test_logout_clears_session(make_web_service) -> None:
    client = registered_client(make_web_service())

    client.post("/cikis")

    assert client.get("/test", follow_redirects=False).status_code == 303


def _checked_choice(html: str) -> list[str]:
    import re

    return re.findall(r'<input type="radio" name="secim" id="(secim-\w+)"\s+checked', html)


def test_home_shows_two_choices_none_open(make_web_service) -> None:
    page = client_for(make_web_service()).get("/").text

    assert 'id="secim-basla"' in page and 'id="secim-sonuc"' in page
    assert _checked_choice(page) == []


def test_register_error_opens_start_choice(make_web_service) -> None:
    page = client_for(make_web_service()).post(
        "/kayit", data={"nickname": "Ali", "pin": "1234", "pin_again": "9999"}
    ).text

    assert _checked_choice(page) == ["secim-basla"]


def test_login_error_opens_result_choice(make_web_service, fake_db) -> None:
    fake_db.reserve_login_attempt.return_value = None
    fake_db.get_participant_by_key.return_value = None

    page = client_for(make_web_service()).post("/giris", data={"nickname": "yok", "pin": "1234"}).text

    assert _checked_choice(page) == ["secim-sonuc"]


def test_result_cards_show_sections_in_order(make_web_service) -> None:
    page = registered_client(make_web_service()).get(f"/sonuc/{PUBLIC_ID}").text
    first_card = page[page.index('class="tarz-kart'):page.index('class="tarz-kart', page.index('class="tarz-kart') + 1)]

    headings = ["Nasıl davranır", "Uygun olduğu koşullar", "Uygun olmadığı koşullar", "Size tavsiyeler", "Karşınızda bu tarzda biri varsa"]
    positions = [first_card.index(h) for h in headings]
    assert positions == sorted(positions)


def test_result_shows_answers_and_answer_key_tabs(make_web_service) -> None:
    page = registered_client(make_web_service()).get(f"/sonuc/{PUBLIC_ID}").text

    assert "Sorulara cevaplarım" in page and "Cevap anahtarım" in page
    key = page[page.index('class="cevap-anahtari'):page.index("</table>", page.index('class="cevap-anahtari'))]
    # 30 soru satırı, her satırda tam bir seçili hücre; altta tasarım örneğinin toplamları.
    assert key.count('class="soru-no"') == 30
    assert key.count("secili") == 30
    assert "<td>9</td><td>7</td><td>6</td><td>3</td><td>5</td>" in key.replace(" ", "").replace("\n", "")


def test_score_table_shows_normal_range_column(make_web_service) -> None:
    page = registered_client(make_web_service()).get(f"/sonuc/{PUBLIC_ID}").text
    table = page[page.index('class="puanlar"'):page.index("</table>", page.index('class="puanlar"'))]

    assert "<th>Normal aralık</th>" in table
    # Orta seviye aralığı: düşük eşik + 1 ile yüksek eşik − 1 (Rekabetçi 3/8 → 4–7).
    for aralik in ["4–7", "6–9", "5–8", "5–7", "4–6"]:
        assert f"<td>{aralik}</td>" in table
    assert "Seviyeler eğitimdeki eşiklere" not in page
