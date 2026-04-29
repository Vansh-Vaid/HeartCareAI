"""ChatbotService — rule-based + optional LLM knowledge-grounded assistant.

Priority:
  1. Emergency keyword detection → immediate safety message
  2. LLM (if OPENAI_API_KEY configured) with retrieved context
  3. Rule-based keyword router → direct short answer
  4. TF-IDF retrieved context → summarised first paragraph
  5. Fallback "not found" message
"""
from __future__ import annotations

import os
import re
from typing import Any

from chatbot.provider import HostedLLMProvider
from chatbot.retriever import KnowledgeRetriever


# ---------------------------------------------------------------------------
# Emergency patterns — always answered immediately, no retrieval needed
# ---------------------------------------------------------------------------
_EMERGENCY_PATTERNS = re.compile(
    r"\b(chest pain|heart attack|can't breathe|cannot breathe|"
    r"shortness of breath|arm pain|jaw pain|call 911|emergency|"
    r"dying|collapse|collapsed)\b",
    re.IGNORECASE,
)

_EMERGENCY_RESPONSE = (
    "If you are having chest pain, shortness of breath, pain spreading to the arm or jaw, "
    "or any other possible heart emergency symptom, call emergency services right away "
    "(911 / 112 / 102 depending on your location). Do not rely on this tool in an emergency."
)

# ---------------------------------------------------------------------------
# Keyword → canonical topic router (short direct answers for common queries)
# ---------------------------------------------------------------------------
_QUICK_ANSWERS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"\b(high risk|what.*high risk|mean.*high risk|positive screen)\b", re.I),
        "A higher-risk result means the screening found a pattern that may need closer medical review. "
        "It does not confirm heart disease, but it is a sign to review symptoms, test results, and next steps with a clinician soon.",
    ),
    (
        re.compile(r"\b(low risk|negative|normal result)\b", re.I),
        "A lower-risk result means the screening did not cross the app's alert level. "
        "That is reassuring, but it does not fully rule out heart disease. If symptoms are present or worsening, medical review is still important.",
    ),
    (
        re.compile(r"\b(threshold|cut.?off|0\.5|decision threshold|why not 0\.5)\b", re.I),
        "The threshold is the app's alert level. It is the point where the result changes from a lower-risk screen to a higher-risk screen. "
        "It is set to be cautious, so the app is less likely to miss people who may need follow-up.",
    ),
    (
        re.compile(r"\b(accuracy|how accurate|reliable|precision|recall|auc)\b", re.I),
        "The screening model was evaluated on held-out data before being used here. "
        "One important measure is recall, which reflects how well the system avoids missing cases that may need attention. "
        "The app is intentionally cautious, so some people may be flagged for follow-up even if later testing is reassuring.",
    ),
    (
        re.compile(r"\b(model|which model|ensemble|random forest|xgboost|logistic|extra tree)\b", re.I),
        "HeartCare AI uses several models behind the scenes to strengthen screening quality. "
        "If you want the simple version, the important part is that the app turns test values into a clearer risk estimate and explanation.",
    ),
    (
        re.compile(r"\b(probability|percent|percentage|confidence|what.*percentage|score mean)\b", re.I),
        "The percentage is the screening model's estimate of how strongly the entered pattern matches cases that may need follow-up. "
        "It is a risk estimate, not a diagnosis. The confidence label tells you how close that estimate is to the app's alert level.",
    ),
    (
        re.compile(r"\b(chest pain type|cp|angina|asymptomatic|typical angina)\b", re.I),
        "Chest pain type describes the kind of chest discomfort a person reports. "
        "Typical angina is the classic pattern linked to heart strain, while asymptomatic means no chest pain is reported. "
        "That information can still matter because some heart problems do not cause obvious pain.",
    ),
    (
        re.compile(r"\b(st depression|oldpeak|st segment)\b", re.I),
        "ST depression is a heart test measurement that looks at how the ECG changes during exercise. "
        "Higher values can be a sign that the heart may be under more strain during activity.",
    ),
    (
        re.compile(r"\b(thal|thalassemia|defect|thallium)\b", re.I),
        "This refers to a coded result from a heart imaging stress test. "
        "It helps describe whether blood flow looked normal or whether there were signs that may need more attention.",
    ),
    (
        re.compile(r"\b(cholesterol|chol|mg.?dl)\b", re.I),
        "Cholesterol is a fat-like substance in the blood. Higher values can increase heart risk over time, which is why it is included in the screening.",
    ),
    (
        re.compile(r"\b(blood pressure|bp|trestbps|hypertens)\b", re.I),
        "Blood pressure is the force of blood pushing against the artery walls. "
        "When it stays high over time, it can place extra strain on the heart and blood vessels.",
    ),
    (
        re.compile(r"\b(max heart rate|thalachh|maximum.*rate|exercise heart)\b", re.I),
        "This is the highest heart rate reached during the exercise test. "
        "It is one of several clues used to understand how the heart responded to activity.",
    ),
    (
        re.compile(r"\b(download|pdf|report)\b", re.I),
        "You can download a PDF report from the result page. "
        "It gives you a summary you can save, print, or review with a doctor later.",
    ),
    (
        re.compile(r"\b(who.*use|intended.*for|patient|doctor|clinician)\b", re.I),
        "HeartCare AI is meant to support patients, clinicians, and other users who need help understanding heart screening information. "
        "It works best when used alongside real clinical data and professional medical review.",
    ),
    (
        re.compile(r"\b(diagnosis|diagnose|replace.*doctor|instead.*doctor)\b", re.I),
        "I can help explain terms and screening results, but I cannot diagnose heart disease or replace a doctor. "
        "Only a clinician can make that decision after reviewing the full medical picture.",
    ),
    (
        re.compile(r"\b(ca|vessels|fluoroscopy|colored vessels)\b", re.I),
        "This field refers to how many major blood vessels were visible during heart imaging. "
        "It can add useful context when reviewing possible heart-related changes.",
    ),
    (
        re.compile(r"\b(fbs|fasting.*sugar|blood sugar|diabetes)\b", re.I),
        "This field checks whether fasting blood sugar was above 120 mg/dL. "
        "Higher blood sugar can matter because diabetes and heart health are often connected.",
    ),
    (
        re.compile(r"\b(restecg|ecg|electrocardiogram|st.?t wave|lv hypertrophy)\b", re.I),
        "A resting ECG records the heart's electrical activity while the patient is at rest. "
        "Changes in that pattern can provide clues about strain or other heart-related issues.",
    ),
    (
        re.compile(r"\b(exang|exercise.*angina|angina.*exercise)\b", re.I),
        "This asks whether chest pain happened during exercise. "
        "That can be an important clue because activity can reveal symptoms that are not obvious at rest.",
    ),
    (
        re.compile(r"\b(slope|st slope|upslop|flat|downslop)\b", re.I),
        "This describes the direction of a part of the ECG line during exercise. "
        "It is a technical feature, but the simple takeaway is that different slope patterns can carry different risk signals.",
    ),
    (
        re.compile(r"\b(data.*stor|privacy|secure|confidential)\b", re.I),
        "Your data is stored inside the app account workflow and used to support screening and reporting. "
        "You should still review your project's privacy and deployment setup if this app is used beyond local or demo use.",
    ),
    (
        re.compile(r"\b(hello|hi|hey|good morning|good evening|greet)\b", re.I),
        "Hello. I'm the HeartCare guide. I can explain medical terms, clarify the result wording, "
        "and help you understand what to review next. Ask me about a field, a percentage, or what a result may mean.",
    ),
    (
        re.compile(r"\b(help|what can you|capabilities|what do you know)\b", re.I),
        "I can help in four main ways:\n"
        "• Explain medical terms in simpler words\n"
        "• Clarify what the risk estimate and confidence wording mean\n"
        "• Explain how the screening flow works\n"
        "• Suggest what to discuss with a clinician next\n\n"
        "I am a guide only, not a doctor.",
    ),
]

_SAFETY_NOTICE = (
    "HeartCare AI is a screening tool only. It cannot diagnose heart disease "
    "or replace a qualified clinician."
)

_PAGE_HINTS = {
    "predict": "You are on the screening form. I can explain any field before you submit.",
    "result": "You are on the result page. I can explain the risk estimate, confidence wording, and possible next steps.",
}


class ChatbotService:
    def __init__(self, knowledge_dir: str) -> None:
        self.retriever = KnowledgeRetriever(knowledge_dir)
        self.provider = HostedLLMProvider()

    def answer(self, question: str, page: str | None = None) -> dict[str, Any]:
        q = question.strip()
        page_hint = _PAGE_HINTS.get(page or "", "")

        # 1. Emergency detection — always first
        if _EMERGENCY_PATTERNS.search(q):
            return {
                "answer": _EMERGENCY_RESPONSE,
                "citations": [],
                "grounded": True,
                "safety_notice": _SAFETY_NOTICE,
                "is_emergency": True,
            }

        # 2. Try LLM with retrieved context
        contexts = self.retriever.retrieve(q, top_k=3)
        if contexts and self.provider.enabled:
            llm_answer = self.provider.generate(q, contexts)
            if llm_answer:
                return {
                    "answer": f"{page_hint}\n\n{llm_answer}" if page_hint and re.search(r"\b(help|what can you|hello|hi|hey)\b", q, re.I) else llm_answer,
                    "citations": [
                        {"source": c["source"], "title": c["title"], "score": c["score"]}
                        for c in contexts
                    ],
                    "grounded": True,
                    "safety_notice": _SAFETY_NOTICE,
                    "is_emergency": False,
                }

        # 3. Rule-based keyword router (fast direct answers)
        for pattern, direct_answer in _QUICK_ANSWERS:
            if pattern.search(q):
                return {
                    "answer": f"{page_hint}\n\n{direct_answer}" if page_hint and re.search(r"\b(help|what can you|hello|hi|hey)\b", q, re.I) else direct_answer,
                    "citations": [],
                    "grounded": True,
                    "safety_notice": _SAFETY_NOTICE,
                    "is_emergency": False,
                }

        # 4. TF-IDF retrieval — return best-matching chunk's first paragraph
        if contexts:
            best = contexts[0]
            # Extract first non-empty paragraph
            paragraphs = [p.strip() for p in best["text"].split("\n\n") if p.strip()]
            snippet = paragraphs[0] if paragraphs else best["text"][:400]
            return {
                "answer": (f"{page_hint}\n\n" if page_hint and re.search(r"\b(help|what can you|hello|hi|hey)\b", q, re.I) else "") + snippet + f"\n\n*(Source: {best['title']})*",
                "citations": [
                    {"source": c["source"], "title": c["title"], "score": c["score"]}
                    for c in contexts
                ],
                "grounded": True,
                "safety_notice": _SAFETY_NOTICE,
                "is_emergency": False,
            }

        # 5. Fallback
        return {
            "answer": (
                "I couldn't find a specific answer to that in my knowledge base. "
                "Try asking about a field on the form, the risk percentage, the confidence label, "
                "or what a higher-risk or lower-risk result means.\n\n"
                "For medical concerns, please consult a qualified healthcare provider."
            ),
            "citations": [],
            "grounded": False,
            "safety_notice": _SAFETY_NOTICE,
            "is_emergency": False,
        }


_CHATBOT: ChatbotService | None = None


def get_chatbot_service() -> ChatbotService:
    global _CHATBOT
    if _CHATBOT is None:
        knowledge_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "chatbot",
            "knowledge",
        )
        _CHATBOT = ChatbotService(knowledge_dir)
    return _CHATBOT
