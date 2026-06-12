class RapidTapSmoother:
    def __init__(self, interval_ms):
        self.interval_ms = max(0, int(interval_ms))
        self.last_update_ms = None
        self.pending_action = None
        self.pending_advance = False
        self.idle_reset_at_ms = None

    def set_interval(self, interval_ms):
        self.interval_ms = max(0, int(interval_ms))

    def request(self, action, advance, now_ms):
        self.idle_reset_at_ms = None
        if self._is_ready(now_ms):
            return self._commit(action, advance, now_ms)
        self.pending_action = action
        self.pending_advance = self.pending_advance or advance
        return None

    def release_to_idle(self, now_ms):
        self.idle_reset_at_ms = now_ms + self.interval_ms

    def poll(self, default_action, has_active_actions, now_ms):
        if self.pending_action is not None and self._is_ready(now_ms):
            transition = self._commit(
                self.pending_action,
                self.pending_advance,
                now_ms,
            )
            if not has_active_actions:
                self.release_to_idle(now_ms)
            return transition

        if (
            not has_active_actions
            and self.pending_action is None
            and self.idle_reset_at_ms is not None
            and now_ms >= self.idle_reset_at_ms
        ):
            self.idle_reset_at_ms = None
            return self._commit(default_action, False, now_ms)
        return None

    def reset(self):
        self.last_update_ms = None
        self.pending_action = None
        self.pending_advance = False
        self.idle_reset_at_ms = None

    def _is_ready(self, now_ms):
        if self.interval_ms == 0 or self.last_update_ms is None:
            return True
        return now_ms - self.last_update_ms >= self.interval_ms

    def _commit(self, action, advance, now_ms):
        self.last_update_ms = now_ms
        self.pending_action = None
        self.pending_advance = False
        return action, advance
