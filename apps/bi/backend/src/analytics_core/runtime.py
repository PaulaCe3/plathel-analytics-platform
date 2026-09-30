"""Single-process resource limits. IP ownership is volatile and never logged."""
from collections import deque
from contextlib import contextmanager
from threading import RLock, BoundedSemaphore
from time import monotonic
from analytics_core.errors import AppError


class RuntimeGuard:
    def __init__(self, settings, clock=monotonic):
        self.settings, self.clock = settings, clock
        self.lock = RLock()
        self.semaphore = BoundedSemaphore(settings.heavy_concurrency)
        self.attempts, self.owners, self.pending = {}, {}, {}

    def check_rate(self, ip):
        with self.lock:
            now = self.clock()
            for key in list(self.attempts):
                while self.attempts[key] and self.attempts[key][0] <= now - 3600:
                    self.attempts[key].popleft()
                if not self.attempts[key]:
                    del self.attempts[key]
            history = self.attempts.setdefault(ip, deque())
            if len(history) >= self.settings.uploads_per_hour:
                raise AppError(code="RATE_LIMITED", http_status=429, message="Alcanzaste el límite de creaciones por hora. Intentá más tarde.")
            history.append(now)

    def prune(self):
        with self.lock:
            root = self.settings.dataset_storage_path
            self.owners = {key: value for key, value in self.owners.items() if (root / key).is_dir()}

    @contextmanager
    def creation(self, ip):
        from analytics_core.sessions.store import ID_PATTERN
        with self.lock:
            self.prune()
            root = self.settings.dataset_storage_path
            active = sum(1 for directory in root.iterdir() if directory.is_dir() and ID_PATTERN.fullmatch(directory.name))
            if active + sum(self.pending.values()) >= self.settings.max_active_sessions or sum(owner == ip for owner in self.owners.values()) + self.pending.get(ip, 0) >= self.settings.max_sessions_per_ip:
                raise AppError(code="SESSION_LIMIT_REACHED", http_status=429, message="Alcanzaste el límite de sesiones activas. Borrá una sesión e intentá nuevamente.")
            self.pending[ip] = self.pending.get(ip, 0) + 1
        committed = []
        try:
            yield committed
            with self.lock:
                for dataset_id in committed:
                    self.owners[dataset_id] = ip
        finally:
            with self.lock:
                self.pending[ip] -= 1
                if not self.pending[ip]: del self.pending[ip]

    @contextmanager
    def heavy(self):
        with self.semaphore:
            yield
