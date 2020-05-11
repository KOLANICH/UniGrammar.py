import typing
import string
from abc import ABC, abstractmethod

from .base import Container, Node, Ref, Wrapper


class _CharClass(ABC):
	__slots__ = ()

	def __init__(self, negative: bool) -> None:
		self.negative = negative  # pylint: disable=assigning-non-slot

	@abstractmethod
	def getRanges(self, grammar=None):
		raise NotImplementedError


class CharClass(Node, _CharClass):
	__slots__ = ("chars", "negative",)

	def __init__(self, chars: str, negative: bool = False) -> None:
		Node.__init__(self)
		_CharClass.__init__(self, negative)
		self.chars = chars

	def getRanges(self, grammar: None = None) -> typing.Iterator[range]:
		for c in self.chars:
			c = ord(c)
			yield range(c, c + 1)

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.chars) + ", " + repr(self.negative) + ")"


class WellKnownChars(Wrapper, _CharClass):
	__slots__ = ("name", "underlyingObj")

	def __init__(self, name: str, negative: bool = False) -> None:  # pylint: disable=super-init-not-called
		self.name = name
		Wrapper.__init__(self, CharClass(getattr(string, name), negative))  # fucking `super` doesn't wor well in the case of multiple inheritance

	def getRanges(self, grammar: None = None) -> typing.Iterator[range]:
		return self.child.getRanges()

	@property
	def negative(self):
		return self.child.negative

	@negative.setter
	def negative(self, v):
		self.child.negative = v

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.negative) + ", " + repr(self.name) + ", " + repr(self.child) + ")"


class CharRange(Node, _CharClass):
	__slots__ = ("range", "negative",)

	def __init__(self, start: str, stop: str, negative: bool = False) -> None:
		Node.__init__(self)
		_CharClass.__init__(self, negative)
		self.range = range(ord(start), ord(stop) + 1)

	@property
	def start(self) -> str:
		return chr(self.range.start)

	@property
	def end(self) -> str:
		"""INCLUSIVE!"""
		return chr(self.range.stop - 1)

	def getRanges(self, grammar: None = None) -> typing.Iterator[range]:
		yield self.range

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.negative) + ", " + repr(self.range) + ")"


class CharClassUnion(Container, _CharClass):
	__slots__ = ("negative",)

	EMPTY_MAKES_SENSE = True

	def __init__(self, *children, negative=False) -> None:
		Container.__init__(self, *children)
		_CharClass.__init__(self, negative)

	def getRanges(self, grammar: typing.Optional["Grammar"] = None) -> None:
		for c in self.children:
			if isinstance(c, Ref):
				yield from grammar.chars.index[c.name].getRanges(grammar)
			else:
				yield from c.getRanges(grammar)

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.negative) + ", " + repr(self.children) + ")"
