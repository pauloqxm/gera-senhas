import secrets
import string

AMBIGUOUS = set("Il1O0|`\'\";:,.")

def generate_password(length=12, use_upper=True, use_lower=True, use_digits=True, use_symbols=False, avoid_ambiguous=True):
    pools = []
    if use_upper: pools.append(string.ascii_uppercase)
    if use_lower: pools.append(string.ascii_lowercase)
    if use_digits: pools.append(string.digits)
    if use_symbols: pools.append("!@#$%^&*()-_=+[]{}<>?/")
    if not pools:
        pools = [string.ascii_letters + string.digits]

    password_chars = [secrets.choice(pool) for pool in pools]
    all_chars = "".join(pools)
    while len(password_chars) < length:
        ch = secrets.choice(all_chars)
        if avoid_ambiguous and ch in AMBIGUOUS:
            continue
        password_chars.append(ch)
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)
