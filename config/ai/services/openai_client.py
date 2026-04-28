from openai import OpenAI
from django.conf import settings


def get_openai_client():
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY o‘rnatilmagan")
    return OpenAI(api_key=api_key)