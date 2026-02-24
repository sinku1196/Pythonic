import time
import sqlite3
import threading
import contextlib
import platform

# ==============================
# Cross-platform file locking
# ==============================

if platform.system() == "Windows":
    import msvcrt

    def lock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def unlock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def lock_file(f):
        fcntl.flock(f, fcntl.LOCK_EX)

    def unlock_file(f):
        fcntl.flock(f, fcntl.LOCK_UN)

# ==============================
# Safe SQLite Manager
# ==============================

class SQLiteManager:
    """
    Fully serialized, cross-process safe SQLite manager.
    Guarantees:
    - Single access at a time (global lock)
    - Atomic transactions
    - Crash-safe OS locking
    - Blocking semantics (no request loss)
    """

    def __init__(self, db_path, lock_path=None, timeout=30.0, retry_delay=0.1):
        self.db_path = db_path
        self.lock_path = lock_path or f"{db_path}.lock"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self._thread_lock = threading.Lock()

        # Ensure lock file exists
        open(self.lock_path, "a").close()

    @contextlib.contextmanager
    def access(self):
        """
        Serialized DB access context.
        Blocks until lock is acquired.
        """
        start = time.time()

        with self._thread_lock:
            with open(self.lock_path, "r+") as lockf:
                # OS-level lock (cross-process safe)
                lock_file(lockf)

                try:
                    conn = sqlite3.connect(
                        self.db_path,
                        timeout=self.timeout,
                        isolation_level="DEFERRED",
                        check_same_thread=False,
                    )

                    # Hard safety pragmas
                    conn.execute("PRAGMA journal_mode=WAL;")
                    conn.execute("PRAGMA synchronous=FULL;")
                    conn.execute("PRAGMA foreign_keys=ON;")
                    conn.execute("PRAGMA busy_timeout=30000;")

                    yield conn

                    conn.commit()

                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    raise

                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    unlock_file(lockf)

    # --------------------------
    # Convenience methods
    # --------------------------

    def execute(self, sql, params=None):
        with self.access() as conn:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            return cur.fetchall()

    def executemany(self, sql, seq):
        with self.access() as conn:
            cur = conn.cursor()
            cur.executemany(sql, seq)

    def transaction(self, fn):
        """
        Run a function inside a fully locked transaction.
        """
        with self.access() as conn:
            return fn(conn)