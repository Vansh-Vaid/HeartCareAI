from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.chatbot import get_chatbot_service


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.route("/ask", methods=["POST"])
def ask() -> tuple[str, int] | tuple[dict, int]:
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    page = str(payload.get("page", "")).strip() or None

    if not question:
        return jsonify({"error": "Question is required."}), 400

    response = get_chatbot_service().answer(question, page=page)
    return jsonify(response), 200
