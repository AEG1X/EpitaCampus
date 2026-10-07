"""Import automatique des cours et fichiers depuis Moodle (API de l'application mobile)."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .crypto import decrypt
from .db import SessionLocal
from .icsync import check_url
from .models import Course, CourseFile, MoodleAccount

log = logging.getLogger("campus.moodle")

# Extensions récupérées automatiquement (les vidéos et archives énormes sont ignorées).
ALLOWED_EXTENSIONS = {"pdf", "pptx", "ppt", "docx", "doc", "odt", "odp", "txt", "md", "c", "h", "py", "zip", "png", "jpg", "jpeg"}
MAX_FILE = 100 * 1024 * 1024


class MoodleError(Exception):
    pass


class MoodleClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.http = httpx.Client(timeout=60)

    def call(self, function: str, **params):
        check_url(self.base_url)
        resp = self.http.post(
            f"{self.base_url}/webservice/rest/server.php",
            data={"wstoken": self.token, "wsfunction": function, "moodlewsrestformat": "json", **params},
        )
        resp.raise_for_status()
        data = resp.json()
        # Moodle renvoie les erreurs avec un code 200 et un champ « exception ».
        if isinstance(data, dict) and "exception" in data:
            raise MoodleError(data.get("message") or data.get("errorcode") or "Erreur Moodle")
        return data

    def site_info(self) -> dict:
        return self.call("core_webservice_get_site_info")

    def download(self, file_url: str, dest) -> int:
        sep = "&" if "?" in file_url else "?"
        size = 0
        with self.http.stream("GET", f"{file_url}{sep}token={self.token}", follow_redirects=True) as resp:
            resp.raise_for_status()
            with dest.open("wb") as out:
                for chunk in resp.iter_bytes(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_FILE:
                        raise MoodleError("fichier trop gros")
                    out.write(chunk)
        return size


def token_from_qr(base_url: str, qr_key: str, moodle_user_id: int) -> str:
    """Échange la clé du QR code de connexion Moodle contre un jeton (comme l'appli mobile).

    Moodle n'accepte l'échange que depuis la même adresse IP que le navigateur qui a affiché
    le QR code, dans les 10 minutes.
    """
    check_url(base_url)
    resp = httpx.post(
        f"{base_url.rstrip('/')}/lib/ajax/service-nologin.php",
        params={"info": "tool_mobile_get_tokens_for_qr_login"},
        json=[
            {
                "index": 0,
                "methodname": "tool_mobile_get_tokens_for_qr_login",
                "args": {"qrloginkey": qr_key, "userid": moodle_user_id},
            }
        ],
        # Moodle réserve cette fonction à l'application mobile.
        headers={"User-Agent": "MoodleMobile 4.5.0 (EpitaCampus)"},
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()[0]
    if result.get("error"):
        exc = result.get("exception", {})
        if exc.get("errorcode") == "ipmismatch":
            raise MoodleError("le QR code doit être affiché sur le même réseau que le site")
        raise MoodleError(exc.get("message") or "QR code refusé")
    return result["data"]["token"]


def files_dir():
    path = settings.data_dir / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sync_account(db: Session, account: MoodleAccount) -> dict:
    """Crée les cours manquants et télécharge les nouveaux fichiers. Renvoie un résumé."""
    client = MoodleClient(account.base_url, decrypt(account.token_encrypted))
    stats = {"courses": 0, "new_courses": 0, "new_files": 0}
    # URL du fichier sur Moodle -> fichier déjà importé
    known = {
        f.moodle_key.rsplit("|", 1)[0]: f
        for f in db.scalars(
            select(CourseFile)
            .join(Course)
            .where(Course.user_id == account.user_id, CourseFile.moodle_key.is_not(None))
        )
    }

    for mc in client.call("core_enrol_get_users_courses", userid=account.moodle_user_id):
        stats["courses"] += 1
        course = db.scalar(
            select(Course).where(Course.user_id == account.user_id, Course.moodle_course_id == mc["id"])
        )
        if course is None:
            course = Course(
                user_id=account.user_id,
                moodle_course_id=mc["id"],
                subject=(mc.get("shortname") or "Moodle")[:100],
                title=(mc.get("fullname") or mc.get("shortname") or "Cours Moodle")[:200],
                next_review=None,
            )
            db.add(course)
            db.flush()
            stats["new_courses"] += 1

        try:
            sections = client.call("core_course_get_contents", courseid=mc["id"])
        except MoodleError as exc:
            log.warning("Contenu du cours %s inaccessible : %s", mc["id"], exc)
            continue

        for section in sections:
            for module in section.get("modules", []):
                for content in module.get("contents") or []:
                    if content.get("type") != "file":
                        continue
                    name = content.get("filename", "")
                    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                    if ext not in ALLOWED_EXTENSIONS or content.get("filesize", 0) > MAX_FILE:
                        continue
                    url = content["fileurl"][:980]
                    key = f"{url}|{content.get('timemodified', 0)}"
                    previous = known.get(url)
                    if previous is not None and previous.moodle_key == key:
                        continue
                    stored = f"{uuid.uuid4().hex}.{ext}"
                    dest = files_dir() / stored
                    try:
                        size = client.download(content["fileurl"], dest)
                    except Exception as exc:  # noqa: BLE001
                        dest.unlink(missing_ok=True)
                        log.warning("Téléchargement impossible de %s : %s", name, exc)
                        continue
                    if previous is not None:
                        # Le professeur a mis à jour le fichier : on remplace l'ancienne version.
                        (files_dir() / previous.stored_name).unlink(missing_ok=True)
                        db.delete(previous)
                    record = CourseFile(
                        course_id=course.id,
                        filename=name[:255],
                        stored_name=stored,
                        size=size,
                        moodle_key=key,
                        section=(section.get("name") or "")[:255] or None,
                    )
                    db.add(record)
                    known[url] = record
                    stats["new_files"] += 1
        db.commit()

    account.last_sync = datetime.now(timezone.utc)
    account.last_error = None
    db.commit()
    return stats


def run_sync(account_id: int) -> None:
    """Lance une synchronisation complète (utilisé en tâche de fond)."""
    with SessionLocal() as db:
        account = db.get(MoodleAccount, account_id)
        if account is None:
            return
        try:
            stats = sync_account(db, account)
            log.info("Moodle synchronisé pour l'utilisateur %s : %s", account.user_id, stats)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            account = db.get(MoodleAccount, account_id)
            account.last_error = str(exc)[:500]
            log.exception("Échec de la synchronisation Moodle")
        finally:
            account.syncing = False
            db.commit()


async def sync_loop() -> None:
    while True:
        await asyncio.sleep(60)  # laisse le serveur démarrer tranquillement
        with SessionLocal() as db:
            ids = list(db.scalars(select(MoodleAccount.id)))
        for account_id in ids:
            await asyncio.to_thread(run_sync, account_id)
        await asyncio.sleep(settings.moodle_sync_hours * 3600)
