from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from conftest import OWNER_ID, PUBLIC_ID
from main import create_app
from step_database import ParticipantSummary


def client_for(service) -> TestClient:
    return TestClient(create_app(service, session_secret="test-secret", cookie_secure=False))


def admin_client(service) -> TestClient:
    client = client_for(service)
    response = client.post("/yonetici", data={"password": "gizli"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/yonetici/adaylar"
    return client


def test_admin_pages_require_login(make_web_service) -> None:
    client = client_for(make_web_service())

    for path in ["/yonetici/adaylar", f"/yonetici/aday/{OWNER_ID}"]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/yonetici"


def test_admin_login_wrong_password(make_web_service) -> None:
    response = client_for(make_web_service()).post("/yonetici", data={"password": "yanlis"})

    assert response.status_code == 400
    assert "Şifre hatalı" in response.text


def test_admin_login_locks_after_five_failures(make_web_service) -> None:
    client = client_for(make_web_service())
    for _ in range(5):
        client.post("/yonetici", data={"password": "yanlis"})

    response = client.post("/yonetici", data={"password": "gizli"}, follow_redirects=False)

    assert response.status_code == 429
    assert "15 dakika" in response.text


def test_admin_candidate_list(make_web_service, fake_db) -> None:
    fake_db.list_participant_summaries.return_value = [
        ParticipantSummary(id=OWNER_ID, nickname="Ali", attempt_count=2, last_attempt_at=datetime(2026, 11, 11, tzinfo=timezone.utc)),
        ParticipantSummary(id=9, nickname="Veli", attempt_count=0, last_attempt_at=None),
    ]
    page = admin_client(make_web_service()).get("/yonetici/adaylar")

    assert page.status_code == 200
    assert "Ali" in page.text and "Veli" in page.text
    assert f"/yonetici/aday/{OWNER_ID}" in page.text


def test_admin_sees_candidate_history_and_result(make_web_service) -> None:
    client = admin_client(make_web_service())

    history = client.get(f"/yonetici/aday/{OWNER_ID}")
    result = client.get(f"/sonuc/{PUBLIC_ID}")

    assert history.status_code == 200 and f"/sonuc/{PUBLIC_ID}" in history.text
    assert "Testi tekrar çöz" not in history.text
    assert result.status_code == 200 and "Rekabetçi · 9" in result.text


def test_admin_unknown_candidate_404(make_web_service, fake_db) -> None:
    fake_db.get_participant.return_value = None

    assert admin_client(make_web_service()).get("/yonetici/aday/999").status_code == 404


def test_admin_no_live_button(make_web_service) -> None:
    client = admin_client(make_web_service(gemini=MagicMock()))

    page = client.get(f"/sonuc/{PUBLIC_ID}").text

    assert "canli-yorum" not in page
    assert 'id="kisisellestir"' not in page


def test_admin_login_via_main_form(make_web_service) -> None:
    client = client_for(make_web_service())

    response = client.post("/giris", data={"nickname": "ustaoglu", "pin": "gizli"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/yonetici/adaylar"
    assert client.get("/yonetici/adaylar").status_code == 200


def test_admin_login_via_main_form_wrong_password(make_web_service, fake_db) -> None:
    client = client_for(make_web_service())

    response = client.post("/giris", data={"nickname": "ustaoglu", "pin": "9999"})

    assert response.status_code == 400
    assert "Takma ad veya PIN hatalı." in response.text
    fake_db.reserve_login_attempt.assert_not_called()
    assert client.get("/yonetici/adaylar", follow_redirects=False).status_code == 303


def test_admin_actions_require_login(make_web_service, fake_db) -> None:
    client = client_for(make_web_service())

    for path, data in [(f"/yonetici/aday/{OWNER_ID}/ad", {"nickname": "Yeni"}), (f"/yonetici/aday/{OWNER_ID}/sil", {})]:
        response = client.post(path, data=data, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/yonetici"
    fake_db.rename_participant.assert_not_called()
    fake_db.delete_participant.assert_not_called()


def test_admin_candidate_list_has_rename_and_delete_forms(make_web_service, fake_db) -> None:
    fake_db.list_participant_summaries.return_value = [
        ParticipantSummary(id=OWNER_ID, nickname="Ali", attempt_count=2, last_attempt_at=None),
    ]
    page = admin_client(make_web_service()).get("/yonetici/adaylar").text

    assert f'action="/yonetici/aday/{OWNER_ID}/ad"' in page
    assert f'action="/yonetici/aday/{OWNER_ID}/sil"' in page
    assert "confirm(" in page


def test_admin_rename_redirects_to_list(make_web_service, fake_db) -> None:
    fake_db.rename_participant.return_value = True

    response = admin_client(make_web_service()).post(
        f"/yonetici/aday/{OWNER_ID}/ad", data={"nickname": "Yeni Ad"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/yonetici/adaylar"
    assert fake_db.rename_participant.call_args.args[:2] == (OWNER_ID, "Yeni Ad")


def test_admin_rename_invalid_shows_message(make_web_service, fake_db) -> None:
    response = admin_client(make_web_service()).post(f"/yonetici/aday/{OWNER_ID}/ad", data={"nickname": "a"})

    assert response.status_code == 400
    assert "Adaylar" in response.text and 'class="hata"' in response.text
    fake_db.rename_participant.assert_not_called()


def test_admin_rename_unknown_candidate(make_web_service, fake_db) -> None:
    fake_db.rename_participant.return_value = False

    response = admin_client(make_web_service()).post(f"/yonetici/aday/{OWNER_ID}/ad", data={"nickname": "Yeni"})

    assert response.status_code == 404


def test_admin_delete_redirects_to_list(make_web_service, fake_db) -> None:
    fake_db.delete_participant.return_value = True

    response = admin_client(make_web_service()).post(f"/yonetici/aday/{OWNER_ID}/sil", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/yonetici/adaylar"
    fake_db.delete_participant.assert_called_once_with(OWNER_ID)


def test_admin_delete_unknown_candidate(make_web_service, fake_db) -> None:
    fake_db.delete_participant.return_value = False

    response = admin_client(make_web_service()).post(f"/yonetici/aday/{OWNER_ID}/sil")

    assert response.status_code == 404
