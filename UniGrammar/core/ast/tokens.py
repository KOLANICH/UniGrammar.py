import typing

from .base import Container, Node, Ref, Wrapper


class Seq(Container):
	"""Represents a sequence of (non-)terminals"""

	__slots__ = ()


class Lit(Node):
	"""Literal, just a string. Usually a keyword."""

	__slots__ = ("value",)

	def __init__(self, value: str) -> None:
		super().__init__()
		self.value = value


class Alt(Container):
	"""Represents an alternative."""

	__slots__ = ()


class Opt(Wrapper):
	"""Represents optionality. We could have introduced `max` for `Iter` instead (max=1 and min=0 replacing this node), but
	* parser generators usually have a distinct syntax node for optionality (usually `?`) and have no syntax for maximal count, so it would require us to detect this situation and work aroud it and process its interaction to `min` correctly
	* we have no support for other `max`s currently
	* this would be not very semantically correct to represent presence/absence of a single node with a collection"""

	__slots__ = ()


class Iter(Wrapper):
	"""Represents repeats. A child must be repeated at least `min` times."""

	__slots__ = ("minCount",)

	def __init__(self, child: typing.Union[Ref, str], minCount: int) -> None:
		super().__init__(child)
		self.minCount = minCount
