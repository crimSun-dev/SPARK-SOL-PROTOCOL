"""One-time Firebase setup for the GitHub Pages viewer with the PC off. Run on the PC.

Uses Flaxeon's own service account (F.L.A.X.E.O.N/config/firebase-service-account.json)
against the `flaxeon` project.

    python cloud_firebase.py plan       # read-only: what apply would change
    python cloud_firebase.py apply      # web app + viewer/firebase-config.js, the Pages domain,
                                        # firebase/firestore.rules (old rules kept in cache/)
    python cloud_firebase.py grant      # after the first Google sign-in on the page:
                                        # lets that account read (spark_access/{uid})
    python cloud_firebase.py grant --existing   # before apply: every account that could
                                        # read under the old rules keeps reading
    python cloud_firebase.py rollback   # put back the rules apply replaced

Google sign-in itself is one switch in the Firebase console, which plan and apply name.
Never prints a key or an email address.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SA = HERE.parent / "config" / "firebase-service-account.json"
RULES = HERE / "firebase" / "firestore.rules"
BACKUP = HERE / "cache" / "firestore.rules.before"
CONFIG_JS = HERE / "viewer" / "firebase-config.js"
PROJECT = "flaxeon"
APP_NAME = "SPARK SOL web viewer"
DOMAIN = "crimsun-dev.github.io"
FB = f"https://firebase.googleapis.com/v1beta1/projects/{PROJECT}"
RULES_API = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT}"
IDT = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT}"
CONSOLE = f"https://console.firebase.google.com/project/{PROJECT}/authentication/providers"


def session():
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_file(
        str(SA), scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(creds)


def ok(r, what):
    if r.status_code >= 300:
        msg = (r.json().get("error") or {}).get("message", "") if r.content else ""
        raise SystemExit(f"{what}: HTTP {r.status_code} {msg[:200]}")
    return r.json() if r.content else {}


def web_app(s, create: bool):
    apps = ok(s.get(FB + "/webApps"), "list web apps").get("apps", [])
    app = next((a for a in apps if a.get("displayName") == APP_NAME), None)
    if app or not create:
        return app
    op = ok(s.post(FB + "/webApps", json={"displayName": APP_NAME}), "create web app")
    for _ in range(30):
        o = ok(s.get("https://firebase.googleapis.com/v1beta1/" + op["name"]), "web app operation")
        if o.get("done"):
            if o.get("error"):
                raise SystemExit("create web app: " + o["error"].get("message", "failed"))
            return o["response"]
        time.sleep(2)
    raise SystemExit("create web app: still running after a minute")


def live_rules(s) -> tuple[str | None, str]:
    rel = ok(s.get(RULES_API + "/releases/cloud.firestore"), "read rules release")
    rs = ok(s.get("https://firebaserules.googleapis.com/v1/" + rel["rulesetName"]), "read ruleset")
    return rel["rulesetName"], rs["source"]["files"][0]["content"]


def release(s, source: str) -> None:
    rs = ok(s.post(RULES_API + "/rulesets",
                   json={"source": {"files": [{"name": "firestore.rules", "content": source}]}}),
            "compile rules")
    ok(s.patch(RULES_API + "/releases/cloud.firestore",
               json={"release": {"name": f"projects/{PROJECT}/releases/cloud.firestore",
                                 "rulesetName": rs["name"]}}), "release rules")


def google_enabled(s) -> bool:
    r = s.get(IDT + "/defaultSupportedIdpConfigs/google.com")
    return r.status_code == 200 and bool(r.json().get("enabled"))


def users_by_kind() -> dict:
    """How many Firebase Auth users of each kind exist, so a rules change locks no one out."""
    import firebase_admin
    from firebase_admin import auth, credentials
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(str(SA)))
    kinds: dict = {}
    for u in auth.list_users().iterate_all():
        provs = sorted(p.provider_id for p in u.provider_data) or ["custom-token"]
        k = ("phone-" if u.uid.startswith("phone-") else "other") + ":" + "+".join(provs)
        kinds[k] = kinds.get(k, 0) + 1
    return kinds


def plan(s) -> None:
    app = web_app(s, create=False)
    print("web app:", "present" if app else "will be created", f"({APP_NAME})")
    domains = ok(s.get(IDT + "/config"), "read auth config").get("authorizedDomains", [])
    print("Pages domain authorised:", "yes" if DOMAIN in domains else "will be added")
    _, live = live_rules(s)
    print("rules:", "already current" if live.strip() == RULES.read_text(encoding="utf-8").strip()
          else f"will be replaced by {RULES.relative_to(HERE)} (the live copy saved to cache/ first)")
    print("Google sign-in:", "on" if google_enabled(s) else f"OFF - switch it on: {CONSOLE}")
    print("Firebase Auth users by kind (only phone- uids and granted accounts read after apply):")
    for k, n in sorted(users_by_kind().items()):
        print(f"  {k}: {n}")


def apply(s) -> None:
    app = web_app(s, create=True)
    cfg = ok(s.get(FB + f"/webApps/{app['appId']}/config"), "read web app config")
    public = {k: cfg[k] for k in ("apiKey", "authDomain", "projectId", "appId") if k in cfg}
    CONFIG_JS.write_text(
        "// Written by cloud_firebase.py. The Firebase web config is public by design:\n"
        "// what anyone may read is decided by firebase/firestore.rules, not by this file.\n"
        "export const FIREBASE_CONFIG = " + json.dumps(public, indent=2) + ";\n", encoding="utf-8")
    print("web app ready; wrote", CONFIG_JS.relative_to(HERE))

    conf = ok(s.get(IDT + "/config"), "read auth config")
    domains = conf.get("authorizedDomains", [])
    if DOMAIN not in domains:
        ok(s.patch(IDT + "/config?updateMask=authorizedDomains",
                   json={"authorizedDomains": domains + [DOMAIN]}), "authorise the Pages domain")
    print("Pages domain authorised:", DOMAIN)

    name, live = live_rules(s)
    new = RULES.read_text(encoding="utf-8")
    if live.strip() != new.strip():
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        if not BACKUP.exists():                 # the first apply keeps the original
            BACKUP.write_text(live, encoding="utf-8")
        release(s, new)
        _, now = live_rules(s)
        if now.strip() != new.strip():
            raise SystemExit("rules: the release did not take")
        print("rules released; the previous rules are in", BACKUP.relative_to(HERE))
    else:
        print("rules already current")
    if not google_enabled(s):
        print("LEFT FOR YOU: switch on Google sign-in:", CONSOLE)


def grant(uid: str | None) -> None:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(str(SA)))
    db = firestore.client()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if uid == "--existing":                     # every account that could read before these rules
        users = [u for u in auth.list_users().iterate_all() if not u.uid.startswith("phone-")]
        for u in users:
            db.collection("spark_access").document(u.uid).set({"granted_at": now, "why": "read before the rules change"})
        missing = [u.uid for u in users if not db.collection("spark_access").document(u.uid).get().exists]
        if missing:
            raise SystemExit(f"grant: {len(missing)} access rows did not save")
        print(f"granted {len(users)} existing account(s)")
        return
    if not uid:
        google = [u for u in auth.list_users().iterate_all()
                  if any(p.provider_id == "google.com" for p in u.provider_data)]
        if len(google) != 1:
            raise SystemExit(f"{len(google)} Google accounts have signed in; pass the uid the page shows: "
                             "python cloud_firebase.py grant <uid>")
        uid = google[0].uid
    auth.get_user(uid)                          # raises if no such user
    db.collection("spark_access").document(uid).set({"granted_at": now})
    if not db.collection("spark_access").document(uid).get().exists:
        raise SystemExit("grant: the access row did not save")
    print("granted:", uid)


def rollback(s) -> None:
    if not BACKUP.exists():
        raise SystemExit("no saved rules in " + str(BACKUP))
    release(s, BACKUP.read_text(encoding="utf-8"))
    print("previous rules released again")


def main(argv) -> int:
    cmd = argv[0] if argv else "plan"
    if cmd == "grant":
        grant(argv[1] if len(argv) > 1 else None)
        return 0
    s = session()
    {"plan": plan, "apply": apply, "rollback": rollback}.get(cmd, lambda _s: print(__doc__))(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
