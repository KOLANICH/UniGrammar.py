import typing
from abc import ABCMeta, abstractmethod
from collections import deque

from ...utils.escapelib import defaultCharClassEscaper, defaultStringEscaper
from ..ast import Characters, Comment, Embed, Fragmented, Grammar, Import, Keywords, MultiLineComment, Productions, Spacer, Tokens
from ..ast.base import Node
from ..ast.characters import CharClass, CharClassUnion, CharRange, WellKnownChars
from ..ast.prods import Cap, Prefer
from ..ast.templates import TemplateInstantiation
from ..ast.tokens import Alt, Iter, Lit, Opt, Seq
from ..CodeGen import CodeGen, CodeGenContext
from ..defaults import ourProjectLink
from ..templater import expandTemplates


class TranspiledResult:
	__slots__ = ("id", "text")

	def __init__(self, iD: str, text: str = None, tests: None = None) -> None:
		self.id = iD
		self.text = text

	def __str__(self):
		return self.text

	def __repr__(self):
		return self.__class__.__name__ + "(" + repr(self.id) + ", " + repr(self.text) + ")"


class GeneratorContext(CodeGenContext):
	__slots__ = ("stack", "section")

	def __init__(self, currentProdName: typing.Optional[str]) -> None:
		self.stack = deque(())
		self.section = None
		super().__init__(currentProdName)


class Generator(CodeGen):
	__slots__ = ()
	META = None
	charClassEscaper = defaultCharClassEscaper
	stringEscaper = defaultStringEscaper
	CONTEXT_CLASS = GeneratorContext

	@classmethod
	def getGreeting(cls, obj: Grammar) -> typing.Iterable[str]:
		if isinstance(cls.META.product.website, str):
			toolWebsiteStr = cls.META.product.website
		elif isinstance(cls.META.product.website, tuple):
			toolWebsiteStr = ", ".join(cls.META.product.website)

		yield from (
			"Generated by UniGrammar (" + ourProjectLink + ")",
			"for " + cls.META.product.name + " (" + toolWebsiteStr + ") DSL",
		)
		yield ""

		if obj.meta.doc:
			for s in obj.meta.doc.split("\n"):
				s = s.strip()
				yield s
		yield ""

		if obj.meta.docRef:
			yield "References:"
			dr = obj.meta.docRef
			if isinstance(dr, str):
				dr = (dr,)
			for s in dr:
				yield "\t" + s.strip()

		if obj.meta.filenameRegExp:
			yield "Use with files which names are matching the regexp: " + obj.meta.filenameRegExp

	@classmethod
	def getHeader(cls, obj: Grammar) -> typing.Iterable[str]:
		yield cls.resolve(MultiLineComment(greetingLine for greetingLine in cls.getGreeting(obj)), obj)
		yield cls.resolve(Spacer(2), obj)

	@classmethod
	def Section(cls, arr: typing.Any, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		ctx.section = arr
		for obj in arr.children:
			yield cls.resolve(obj, grammar, ctx)

	@classmethod
	@abstractmethod
	def _Name(cls, k: str, v: str) -> str:
		raise NotImplementedError

	@classmethod
	def Name(cls, obj: typing.Any, grammar: typing.Optional["Grammar"], ctx: typing.Any = None) -> str:
		nm = obj.name
		expr = obj.child
		section = ctx.section
		ctx = ctx.spawn()
		ctx.currentProdName = nm
		ctx.section = section
		return cls._Name(nm, cls.resolve(expr, grammar, ctx), ctx)

	@classmethod
	def resolve(cls, obj: typing.Any, grammar: typing.Optional["Grammar"], ctx: typing.Any = None) -> str:
		if isinstance(obj, str):
			return obj

		if not isinstance(obj, Node):
			raise ValueError("This stuff must be a Node", obj)

		clsNm = type(obj).__name__
		processor = getattr(cls, clsNm)
		# ToDo: split into a separate methods, one having nothing to do with ctx and another one using it
		if ctx:
			ctx.stack.append(obj)
		res = processor(obj, grammar, ctx)
		if ctx:
			ctx.stack.pop()
		return res 

	@classmethod
	def Characters(cls, obj: Characters, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		return cls.Section(obj, grammar, ctx)

	@classmethod
	def Keywords(cls, obj: Keywords, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		return cls.Section(obj, grammar, ctx)

	@classmethod
	def Tokens(cls, obj: Tokens, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		return cls.Section(obj, grammar, ctx)

	@classmethod
	def Productions(cls, obj: Productions, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		return cls.Section(obj, grammar, ctx)

	@classmethod
	def Fragmented(cls, obj: Fragmented, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterator[str]:
		return cls.Section(obj, grammar, ctx)

	@classmethod
	def Seq(cls, obj: Seq, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls._Seq(obj.children, grammar, ctx)

	@classmethod
	def _Seq(cls, arr: typing.Iterable[Node], grammar: Grammar, ctx: typing.Any = None) -> str:
		return " ".join(cls.resolve(c, grammar, ctx) for c in arr)

	@classmethod
	def Lit(cls, obj: Lit, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls.wrapLiteralString(obj.value)

	@classmethod
	def wrapLiteralString(cls, s: str) -> str:
		return '"' + cls.stringEscaper(s) + '"'

	@classmethod
	def wrapLiteralChar(cls, s: str) -> str:
		wrapped = cls.wrapLiteralString(s)
		return wrapped

	@classmethod
	def Iter(cls, obj: Iter, grammar: Grammar, ctx: typing.Any = None) -> str:
		ch = cls.resolve(obj.child, grammar, ctx)
		minCount = obj.minCount
		# pylint: disable=no-else-return
		if minCount == 0:
			return cls.wrapZeroOrMore(ch, grammar)
		elif minCount == 1:
			return cls.wrapOneOrMore(ch, grammar)
		return cls.wrapNOrMore(minCount, ch, grammar)

	@classmethod
	@abstractmethod
	def wrapZeroOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def wrapZeroOrOne(cls, res: str, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def wrapOneOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError()

	@classmethod
	def wrapNOrMore(cls, minCount: int, res: str, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls._Seq([res] * minCount + [cls.wrapZeroOrMore(res, grammar)], grammar)

	@classmethod
	def Opt(cls, obj: Opt, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls.wrapZeroOrOne(cls.resolve(obj.child, None, ctx), grammar, ctx)

	@classmethod
	@abstractmethod
	def _Cap(cls, k: str, v: str) -> str:
		raise NotImplementedError

	@classmethod
	def Cap(cls, obj: Cap, grammar: typing.Optional[Grammar], ctx: typing.Any = None) -> str:
		return cls._Cap(obj.name, cls.resolve(obj.child, grammar, ctx))

	@classmethod
	def Prefer(cls, obj: Prefer, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls._Prefer(cls.resolve(obj.child, grammar, ctx), obj.preference, grammar)

	@classmethod
	def _Prefer(cls, res: str, preference: str, grammar: Grammar, ctx: typing.Any = None) -> str:
		return res

	@classmethod
	def Spacer(cls, obj: Spacer, grammar: Grammar, ctx: typing.Any = None) -> str:
		return "\n" * (obj.count - 1)  # we join lines, so an empty line without \n counts

	############

	@classmethod
	@abstractmethod
	def _Comment(cls, comment: str) -> str:
		raise NotImplementedError

	@classmethod
	def Comment(cls, obj: Comment, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls._Comment(obj.value)

	@classmethod
	def MultiLineComment(cls, obj: MultiLineComment, grammar: Grammar, ctx: typing.Any = None) -> str:
		return "\n".join((cls._Comment(line) if line else "") for line in obj.value)

	@classmethod
	@abstractmethod
	def CharClass(cls, obj: CharClass, grammar: Grammar):
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def WellKnownChars(cls, obj: WellKnownChars, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError

	@classmethod
	@abstractmethod
	def CharClassUnion(cls, obj: CharClassUnion, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError

	@classmethod
	@abstractmethod
	def CharRange(cls, obj: CharRange, grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError

	@classmethod
	def Alt(cls, obj: Alt, grammar: Grammar, ctx: typing.Any = None) -> str:
		return cls._wrapAlts((cls.resolve(c, grammar, ctx) for c in obj.children), grammar)

	@classmethod
	@abstractmethod
	def _wrapAlts(cls, alts: typing.Iterable[str], grammar: Grammar, ctx: typing.Any = None) -> str:
		raise NotImplementedError()

	@classmethod
	def preprocessGrammar(cls, grammar: Grammar, ctx: typing.Any = None) -> None:
		expandTemplates(grammar, cls, ctx, grammar)

	@classmethod
	def TemplateInstantiation(cls, obj: TemplateInstantiation, grammar: Grammar, ctx: typing.Any = None) -> typing.Any:
		raise Exception("There must be no templates when we are generating code. They must be already expanded")

	@classmethod
	@abstractmethod
	def embedGrammar(cls, obj: Grammar, ctx: typing.Any = None) -> typing.Any:
		"""Embeds content of a grammar into current transpiled document. Used when creating a new document too."""
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def _Import(cls, obj: Embed, embedIntermediateRepr: typing.Any, ctx: typing.Any = None) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def Import(cls, obj: Import, ctx: typing.Any = None) -> typing.Any:
		raise NotImplementedError()
		#return cls.embedGrammar(g, ctx)

	@classmethod
	def initContext(cls, grammar):
		return cls.CONTEXT_CLASS(None)

	@classmethod
	@abstractmethod
	def _transpile(cls, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		"""A function generating lines of the source. Redefine it in subclasses."""
		raise NotImplementedError()
