from src.models.db.handler_fb_db import ConnectionDBFireBird


def conexao_firebird_manual():
    with ConnectionDBFireBird() as con:
        cur = con.cursor()
        cur.execute("SELECT 1 FROM RDB$DATABASE")
        result = cur.fetchone()
        cur.close()
        return bool(result)


if __name__ == "__main__":
    raise SystemExit(0 if conexao_firebird_manual() else 1)
