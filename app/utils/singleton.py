from typing import Any


class Singleton(type):
    _instances = {}

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwds)
        return self._instances[self]
