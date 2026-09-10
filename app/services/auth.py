import re
import bcrypt


TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}

CYRILLIC = re.compile(r'[А-Яа-яЁё]')

def transliterate(text: str) -> str:
    result = []
    for ch in text.lower():
        if ch in TRANSLIT_MAP:
            result.append(TRANSLIT_MAP[ch])
        elif ch.isascii() and ch.isalpha():
            result.append(ch)
    return ''.join(result)

def generate_login(first_name: str, last_name: str) -> str:
    first = transliterate(first_name)
    last = transliterate(last_name)
    if not first or not last:
        return ""
    return f"{first[0]}.{last}"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if CYRILLIC.search(password):
        return False, "Пароль должен содержать только латиницу"
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать минимум 1 заглавную латинскую букву"
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать минимум 1 цифру"
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Пароль должен содержать минимум 1 специальный символ"
    return True, ""
