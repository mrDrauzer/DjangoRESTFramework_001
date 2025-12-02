from urllib.parse import urlparse

from rest_framework import serializers


def validate_youtube_url(value: str):
    """
    Allow only youtube.com (and youtu.be) links for video URLs.
    Empty values are allowed (field may be optional).
    """
    if not value:
        return value

    try:
        parsed = urlparse(value)
    except Exception:
        raise serializers.ValidationError("Некорректная ссылка")

    host = (parsed.hostname or '').lower()

    allowed_hosts = {
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'youtu.be',
        'www.youtu.be',
    }

    if host not in allowed_hosts:
        raise serializers.ValidationError(
            'Разрешены только ссылки на youtube.com или youtu.be'
        )

    return value
