from flask import Blueprint, jsonify
from dotenv import load_dotenv
import requests
import os

load_dotenv()

exames_pacs_bp = Blueprint("exames_pacs", __name__, url_prefix="/exames-pacs")

@exames_pacs_bp.route("/<int:id>", methods=["POST"])
def busca_exames_pacs(id: int):
    url = os.getenv("URL_EXAMES_PACS")
    token = os.getenv("TOKEN_EXAMES_PACS")

    if not url:
        return jsonify({"error": "URL_EXAMES_PACS não configurada"}), 500

    if not token:
        return jsonify({"error": "TOKEN_EXAMES_PACS não configurado"}), 500

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = {
        "treatmentId": str(id)
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        response.raise_for_status()

        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return jsonify({
                "content_type": response.headers.get("Content-Type"),
                "text": response.text,
            }), response.status_code

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502