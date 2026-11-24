"""Simple offline authentication (local JSON user store, salted PBKDF2 password hashes)."""
import hashlib, hmac, json, os, re, secrets

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.json")
ITERATIONS = 120_000


def _load():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def register(username, name, email, password, confirm):
    """Create an account. Returns (ok, message)."""
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,20}", username):
        return False, "Username must be 3-20 characters: letters, numbers, . _ -"
    if not name.strip():
        return False, "Please enter your full name."
    if email and (not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip())):
        return False, "Enter a valid email or leave it blank."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm:
        return False, "Passwords do not match."
    users = _load()
    if username in users:
        return False, "That username is already taken."
    salt = secrets.token_hex(16)
    users[username] = {"name": name.strip(), "email": email.strip(),
                       "salt": salt, "hash": _hash(password, salt)}
    _save(users)
    return True, "Account created."


def authenticate(username, password):
    """Returns the user record (with 'username') or None."""
    username = username.strip().lower()
    user = _load().get(username)
    if not user:
        return None
    if hmac.compare_digest(user["hash"], _hash(password, user["salt"])):
        return {"username": username, "name": user["name"], "email": user["email"]}
    return None
