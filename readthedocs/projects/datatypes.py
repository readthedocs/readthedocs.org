"""Simple datatypes defined using dataclasses, for describing project data.

Contrast this with the similar 'models' module, which defines Pydantic model
classes.
"""

from __future__ import annotations

import dataclasses
import functools
import sys
import typing


if typing.TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


@dataclasses.dataclass
class ProjectVersionInfo:
    """
    Version information for a project associated with a branch or tag.

    The name fields is the end-user facing description, e.g., as seen in the
    version selector menu.

    The identifier identifies the source for the build, e.g., a branch or
    commit hash.
    """

    verbose_name: str
    identifier: str

    @classmethod
    def serialize_many(cls, data: typing.Sequence[Self]) -> list[dict[str, str]]:
        r"""
        A preparatory step which converts a sequence of ``ProjectVersionInfo``\s into a
        format suitable for JSON serialization.
        """
        return [dataclasses.asdict(item) for item in data]

    @classmethod
    def parse_many(cls, *argument_names: str) -> typing.Callable[..., typing.Any]:
        """
        A decorator which adds a parsing step to deserialize JSON-ified data.

        The keyword argument names which will be targetted for parsing must be supplied
        as strings to ``parse_many()``.
        """

        def decorator(func: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:
            @functools.wraps(func)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                for name in argument_names:
                    if name not in kwargs:
                        raise TypeError(f"Missing required argument: {name}")
                    kwargs[name] = [
                        item if isinstance(item, ProjectVersionInfo) else cls(**item)
                        for item in kwargs[name]
                    ]
                return func(*args, **kwargs)

            return wrapper

        return decorator
