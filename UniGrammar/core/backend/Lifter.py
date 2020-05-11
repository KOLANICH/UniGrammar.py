import typing
from collections import OrderedDict

from ..ast.base import *
from ..ast.characters import *
from ..ast.tokens import *
from ..ast.prods import *
from ..ast import *


class InsertionAction:
	__slots__ = ("sect", "key")

	@property
	def element(self):
		return self.sect[self.key]

	def __init__(self, sect, key):
		self.sect = sect
		self.key = key

	def __repr__(self):
		return repr(self.sect) + "<-[" + repr(self.key) + "]"


class LiftingSection(OrderedDict):
	__slots__ = ("name", "ctx",)

	def __init__(self, name: str, ctx):
		self.name = name
		self.ctx = ctx

	@property
	def parentSect(self):
		return getattr(self.ctx.parent, self.name)

	def __getitem__(self, k):
		try:
			return super().__getitem__(k)
		except KeyError:
			if self.ctx.parent is not None:
				return self.parentSect[k]
			else:
				raise

	def setIndirect(self, k, v):
		#print(self.ctx.label, "setIndirect", k, v)
		insAct = InsertionAction(self, k)
		assert k not in self
		super().__setitem__(k, v)
		assert self[k] is v
		self.ctx.insertionOrder.append(insAct)

		if self.ctx.parent:
			getattr(self.ctx.parent, self.name).setIndirect(k, v)

		return insAct

	def __setitem__(self, k, v):
		insAct = self.setIndirect(k, v)
		self.ctx.directInsertionOrder.append(insAct)

	def __len__(self):
		return super().__len__() + (len(self.parentSect) if self.ctx.parent else 0)


class LiftingContext:
	sectsDicsNames = ("chars", "keywords", "fragmented", "tokens", "prods")
	__slots__ = sectsDicsNames + ("insertionOrder", "directInsertionOrder", "parent", "label")
	SECTION_TYPE = LiftingSection

	def __init__(self, label=None):
		self.parent = None
		self.insertionOrder = []
		self.directInsertionOrder = []
		self.label = label
		for nm in self.__class__.sectsDicsNames:
			setattr(self, nm, self.__class__.SECTION_TYPE(nm, self))

	def spawn(self, label=None):
		newCtx = self.__class__(label)
		newCtx.parent = self
		return newCtx


class Lifter:
	__slots__ = ()
	CONTEXT_TYPE = LiftingContext

	def __call__(self, originalGrammar: typing.Any) -> Grammar:
		raise NotImplementedError
