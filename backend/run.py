import os

from src import create_app

VERDE = "\033[32m"
AMARELO = "\033[33m"
VERMELHO = "\033[31m"
RESET = "\033[0m"

app = create_app()

if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes", "on")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    
    if not debug or os.getenv("WERKZEUG_RUN_MAIN") == "true":
        print(f" * {VERDE}API running on{RESET} {VERMELHO}http://{host}:{port}{RESET}")

    app.run(host=host, port=port, debug=debug)
