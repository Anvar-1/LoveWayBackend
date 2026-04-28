import base64
from django.conf import settings
from .openai_client import get_openai_client


def file_to_data_url(uploaded_file) -> str:
    content = uploaded_file.read()
    uploaded_file.seek(0)

    mime_type = getattr(uploaded_file, "content_type", None) or "image/jpeg"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def moderate_image(uploaded_file) -> dict:
    client = get_openai_client()
    image_data_url = file_to_data_url(uploaded_file)

    result = client.moderations.create(
        model=settings.OPENAI_MODERATION_MODEL,
        input=[
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url
                }
            }
        ]
    )

    output = result.results[0]
    categories = output.categories
    scores = output.category_scores

    return {
        "flagged": bool(output.flagged),
        "sexual": bool(getattr(categories, "sexual", False)),
        "sexual_minors": bool(getattr(categories, "sexual_minors", False)),
        "scores": {
            "sexual": float(getattr(scores, "sexual", 0.0)),
            "sexual_minors": float(getattr(scores, "sexual_minors", 0.0)),
        }
    }