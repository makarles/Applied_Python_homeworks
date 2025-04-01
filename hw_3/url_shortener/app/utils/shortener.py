import string, random
from url_shortener.app.db.models import Link

def generate_short_code(db, length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not db.query(Link).filter(Link.short_code == code).first():
            return code