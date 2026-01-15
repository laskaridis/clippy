from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """SessionAuthentication that skips CSRF validation.

    This is intended for first-party clients like the Chrome extension that
    cannot satisfy Django's Origin-based CSRF checks (e.g., chrome-extension://).
    """

    def enforce_csrf(self, request):  # pragma: no cover - thin wrapper
        return None
