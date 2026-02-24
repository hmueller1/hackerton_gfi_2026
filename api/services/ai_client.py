"""M2-03 + M2-04: OpenAI API Anbindung mit Retry-Logik und sauberem Fallback."""
import logging
import os
import time

logger = logging.getLogger(__name__)

OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gemini-3-pro-preview")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None   # None → OpenAI Standard
OPENAI_TIMEOUT  = int(os.getenv("OPENAI_TIMEOUT", "60"))
_MAX_VERSUCHE   = 3
_BACKOFF_SEK    = [2, 4, 10]


class KiNichtVerfuegbarError(Exception):
    """Wird geworfen wenn die OpenAI API nach allen Retries nicht erreichbar ist."""


def call_claude(
    system_prompt: str,
    user_prompt: str,
    model: str = OPENAI_MODEL,
    max_tokens: int = 8192,
) -> str:
    """
    Ruft die OpenAI Chat-Completions API auf.

    Retry-Logik: max. 3 Versuche mit exponentiellem Backoff (2s / 4s / 10s).
    API-Key fehlt oder alle Versuche fehlgeschlagen → KiNichtVerfuegbarError.

    Returns:
        Textinhalt der ersten Choice.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise KiNichtVerfuegbarError(
            "OPENAI_API_KEY nicht gesetzt. KI-Konfig-Schritt deaktiviert."
        )

    try:
        from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError
    except ImportError as exc:
        raise KiNichtVerfuegbarError(
            "Paket 'openai' nicht installiert. Bitte: pip install openai"
        ) from exc

    client_kwargs = {"api_key": api_key, "timeout": OPENAI_TIMEOUT}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    client = OpenAI(**client_kwargs)
    letzter_fehler: Exception | None = None

    for versuch in range(1, _MAX_VERSUCHE + 1):
        try:
            t0 = time.monotonic()
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            dauer_ms  = int((time.monotonic() - t0) * 1000)
            token_in  = response.usage.prompt_tokens
            token_out = response.usage.completion_tokens
            logger.info(
                "OpenAI API: %dms, %d+%d Tokens (Versuch %d/%d)",
                dauer_ms, token_in, token_out, versuch, _MAX_VERSUCHE,
            )
            return response.choices[0].message.content

        except RateLimitError as exc:
            letzter_fehler = exc
            logger.warning("OpenAI RateLimitError (Versuch %d/%d): %s", versuch, _MAX_VERSUCHE, exc)
        except APIConnectionError as exc:
            letzter_fehler = exc
            logger.warning("OpenAI Verbindungsfehler (Versuch %d/%d): %s", versuch, _MAX_VERSUCHE, exc)
        except APIStatusError as exc:
            letzter_fehler = exc
            logger.warning("OpenAI API-Fehler %d (Versuch %d/%d): %s", exc.status_code, versuch, _MAX_VERSUCHE, exc)
            # 4xx (außer 429) nicht nochmal versuchen
            if exc.status_code < 500 and exc.status_code != 429:
                break

        if versuch < _MAX_VERSUCHE:
            warte = _BACKOFF_SEK[versuch - 1]
            logger.info("Warte %ds vor nächstem Versuch...", warte)
            time.sleep(warte)

    raise KiNichtVerfuegbarError(
        f"OpenAI API nach {_MAX_VERSUCHE} Versuchen nicht erreichbar: {letzter_fehler}"
    )
