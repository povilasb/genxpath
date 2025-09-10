from datetime import timedelta
import typing as t
import time
from pathlib import Path
from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    value: t.Any
    expires_at: int


class Cache(BaseModel):
    """A cache for the data sources.

    e.g. some data sources will make requests to external APIs, like weather forecast.
    To avoid making the same request multiple times, we can cache the results.
    """

    data: dict[str, CacheEntry]
    path: Path = Field(exclude=True, default_factory=lambda: Path.cwd() / "cache.json")

    @classmethod
    def load(cls, path: str) -> t.Self:
        path_ = Path(path)
        if path_.exists():
            return cls.model_validate_json(path_.read_bytes())

        return cls(data={}, path=path_)

    def get(self, key: str) -> str | None:
        if not (entry := self.data.get(key)):
            return None

        if entry.expires_at < time.time():
            return None

        return entry.value

    def set(self, key: str, value: str, expires_in: timedelta) -> None:
        self.data[key] = CacheEntry(
            value=value, expires_at=int(time.time() + expires_in.total_seconds())
        )
        self._persist()

    def _persist(self) -> None:
        self.path.write_bytes(self.model_dump_json(indent=2).encode("utf-8"))
