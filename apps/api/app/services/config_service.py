# =============================================================================
# DataPrismAI — Runtime Configuration Service
# =============================================================================
# Provides a thread-safe, DB-backed configuration cache.
#
# Priority order (highest → lowest):
#   1. DB override  (app_config table, written via /config PATCH)
#   2. Environment variable (env_var field on ConfigEntry, or general env)
#   3. Hardcoded default  (default field on ConfigEntry)
#
# All callers should use:
#   from app.services.config_service import config_svc
#
#   config_svc.get("llm.model")
#   config_svc.get_bool("guardrail.enabled")
#   config_svc.get_int("starrocks.pool_size")
# =============================================================================

from __future__ import annotations

import logging
import threading
from typing import Any

from app.core.config_schema import CONFIG_MAP, CONFIG_ENTRIES, SECTION_META, ConfigEntry

logger = logging.getLogger(__name__)


class ConfigService:
    """Thread-safe configuration service backed by Postgres app_config table."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}   # key → raw string value (DB overrides)
        self._loaded: bool = False
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Load all rows from app_config into the local cache."""
        try:
            from app.db.session import SessionLocal
            from app.db.models import AppConfig
            db = SessionLocal()
            try:
                rows = db.query(AppConfig).all()
                self._cache = {r.key: r.value for r in rows}
                self._loaded = True
                logger.info("ConfigService: loaded %d overrides from DB", len(self._cache))
            finally:
                db.close()
        except Exception as exc:
            logger.warning("ConfigService: DB load failed (%s); using env/defaults only", exc)
            self._cache = {}
            self._loaded = True  # Don't retry every call — use env/defaults

    # ------------------------------------------------------------------
    # Core getters
    # ------------------------------------------------------------------

    def get(self, key: str, fallback: str | None = None) -> str:
        """Return the effective string value for key."""
        self._ensure_loaded()
        # 1. DB override
        if key in self._cache:
            return self._cache[key]
        # 2. ConfigEntry env-var / default
        entry = CONFIG_MAP.get(key)
        if entry:
            return entry.env_default()
        # 3. Caller fallback
        if fallback is not None:
            return fallback
        raise KeyError(f"Unknown config key: {key!r}")

    def get_bool(self, key: str, fallback: bool = False) -> bool:
        try:
            return self.get(key).lower() in ("true", "1", "yes", "on")
        except KeyError:
            return fallback

    def get_int(self, key: str, fallback: int = 0) -> int:
        try:
            return int(self.get(key))
        except (KeyError, ValueError):
            return fallback

    def get_float(self, key: str, fallback: float = 0.0) -> float:
        try:
            return float(self.get(key))
        except (KeyError, ValueError):
            return fallback

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Persist a config override to DB and update local cache."""
        from app.db.session import SessionLocal
        from app.db.models import AppConfig

        self._ensure_loaded()

        entry = CONFIG_MAP.get(key)
        if entry and entry.is_readonly:
            raise ValueError(f"Config key {key!r} is read-only and cannot be changed via the API.")

        db = SessionLocal()
        try:
            row = db.query(AppConfig).filter(AppConfig.key == key).first()
            if row:
                row.value = value
            else:
                db.add(AppConfig(key=key, value=value))
            db.commit()
            with self._lock:
                self._cache[key] = value
        finally:
            db.close()

    def set_many(self, updates: dict[str, str]) -> None:
        """Persist multiple config overrides atomically."""
        for key, value in updates.items():
            entry = CONFIG_MAP.get(key)
            if entry and entry.is_readonly:
                raise ValueError(f"Config key {key!r} is read-only.")
        from app.db.session import SessionLocal
        from app.db.models import AppConfig

        self._ensure_loaded()

        db = SessionLocal()
        try:
            for key, value in updates.items():
                row = db.query(AppConfig).filter(AppConfig.key == key).first()
                if row:
                    row.value = value
                else:
                    db.add(AppConfig(key=key, value=value))
            db.commit()
            with self._lock:
                self._cache.update(updates)
            logger.info("ConfigService: saved %d keys to DB", len(updates))
        finally:
            db.close()

    def reset(self, key: str) -> None:
        """Remove a DB override — effective value reverts to env/default."""
        from app.db.session import SessionLocal
        from app.db.models import AppConfig

        db = SessionLocal()
        try:
            db.query(AppConfig).filter(AppConfig.key == key).delete()
            db.commit()
            with self._lock:
                self._cache.pop(key, None)
        finally:
            db.close()

    def refresh(self) -> None:
        """Force reload from DB (call after external DB changes)."""
        with self._lock:
            self._loaded = False
        self._ensure_loaded()

    # ------------------------------------------------------------------
    # Structured config for the API
    # ------------------------------------------------------------------

    def get_all_sections(self) -> dict:
        """Return full config metadata grouped by section for the frontend."""
        self._ensure_loaded()

        sections: dict[str, dict] = {}
        for entry in CONFIG_ENTRIES:
            s = entry.section
            if s not in sections:
                meta = SECTION_META.get(s, {})
                sections[s] = {
                    "id":          s,
                    "label":       meta.get("label", s.title()),
                    "icon":        meta.get("icon", "⚙"),
                    "description": meta.get("description", ""),
                    "entries":     [],
                }

            effective = self.get(entry.key)
            display_value = "••••••••" if entry.is_sensitive and effective else effective

            sections[s]["entries"].append({
                "key":          entry.key,
                "label":        entry.label,
                "description":  entry.description,
                "value":        display_value,
                "default":      entry.default,
                "input_type":   entry.input_type,
                "options":      entry.options,
                "is_readonly":  entry.is_readonly,
                "is_sensitive": entry.is_sensitive,
                "restart_req":  entry.restart_req,
                "overridden":   entry.key in self._cache,
            })

        return {
            "sections": list(sections.values()),
            "total_keys": len(CONFIG_ENTRIES),
            "overridden_keys": len(self._cache),
        }


# Module-level singleton
config_svc = ConfigService()
