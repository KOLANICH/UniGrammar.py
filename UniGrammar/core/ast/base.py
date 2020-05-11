import typing
from collections.abc import Iterable


class Node:
	"""Just a node of our AST"""

	__slots__ = ()

	def __init__(self) -> None:
		pass


class Collection(Node, Iterable):
	"""A node of AST that can have multiple children"""

	EMPTY_MAKES_SENSE = False

	__slots__ = ("children",)

	def __init__(self, children: Node) -> None:
		super().__init__()
		self.children = children

	def __len__(self) -> int:
		return len(self.children)

	def __iter__(self) -> typing.Iterable[Node]:
		yield from self.children

	def __getitem__(self, k: int) -> Node:
		return self.children[k]

	def __setitem__(self, k, v):
		self.children[k] = v

	def __delitem__(self, k):
		del self.children[k]


class Wrapper(Node):
	"""A node of AST which has exactly one child"""

	__slots__ = ("child",)

	def __init__(self, child: Node) -> None:
		super().__init__()
		self.child = child


class Container(Collection):
	__slots__ = ()

	def __init__(self, *children) -> None:
		super().__init__(children)


class Name(Wrapper):
	"""Assigns a name/id to a (non-)terminal"""

	__slots__ = ("name",)

	def __init__(self, name: str, child: Node) -> None:
		self.name = name
		super().__init__(child)


class Ref(Node):
	"""Represents a reference to another (non-)terminal"""

	__slots__ = ("name",)

	def __init__(self, name: Node) -> None:
		super().__init__()
		self.name = name

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.name) + ")"
