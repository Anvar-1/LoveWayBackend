import json
from django.conf import settings
from .openai_client import get_openai_client


def suggest_replies(message: str, conversation=None, tone: str = "friendly"):
    client = get_openai_client()
    conversation = conversation or []

    prompt = f"""
Sen dating app ichidagi AI chat yordamchisan.
Foydalanuvchiga odobli, qisqa, tabiiy va qiziqarli 3 ta javob variantlari ber.
Til: o'zbek.
Ohang: {tone}.

Oxirgi xabar: {message}

Faqat JSON qaytar:
{{
  "replies": ["variant1", "variant2", "variant3"]
}}
"""

    response = client.responses.create(
        model=settings.OPENAI_CHAT_MODEL,
        input=prompt
    )

    raw_text = response.output_text.strip()
    print("OPENAI RAW RESPONSE:", raw_text)

    try:
        data = json.loads(raw_text)
        replies = data.get("replies", [])
        if not isinstance(replies, list):
            raise ValueError("`replies` list emas")
        return replies[:3]
    except Exception:
        return [
            "Salom 🙂 yaxshimisiz?",
            "Yaxshi, sizda nima gap?",
            "Siz bilan gaplashish yoqimli ekan."
        ]