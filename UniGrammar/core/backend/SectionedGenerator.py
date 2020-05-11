import typing
from abc import ABC, abstractmethod
from collections import defaultdict

from ..ast import Comment, Grammar, Spacer
from .Generator import Generator, GeneratorContext
from .UsualGenerator import UsualGenerator

HalfFinishedReprT = typing.DefaultDict[str, typing.List[str]]


class SectionDumper(ABC):
	__slots__ = ()

	@abstractmethod
	def dumpSection(self, backend: Generator, gr: Grammar, content: typing.Iterable[str], ctx: typing.Any = None):
		raise NotImplementedError

	@abstractmethod
	def dumpContent(self, backend: Generator, gr: Grammar, ctx: typing.Any = None):
		raise NotImplementedError


class UsualSectionDumper(SectionDumper):
	__slots__ = ("friendlyName", "propName", "backendProcessorFuncName")

	def __init__(self, friendlyName: str, propName: str, backendProcessorFuncName: str) -> None:
		super().__init__()
		self.friendlyName = friendlyName
		self.propName = propName
		self.backendProcessorFuncName = backendProcessorFuncName

	def dumpSection(self, backend: Generator, gr: Grammar, content: typing.Iterable[str], ctx: typing.Any = None) -> typing.Iterator[str]:
		if content:
			yield backend.resolve(Comment(self.friendlyName), gr, ctx)
			yield from content
			yield backend.resolve(Spacer(2), gr, ctx)

	def dumpContent(self, backend: Generator, gr: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		sectionObject = getattr(gr, self.propName)
		if sectionObject:
			backendSectionProcessor = getattr(backend, self.backendProcessorFuncName)
			yield from backendSectionProcessor(sectionObject, gr, ctx)


class Sectioner:
	@classmethod
	def START(cls, backend: Generator, gr: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		return backend.getHeader(gr)

	@classmethod
	def END(cls, backend: Generator, gr: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		return ()

	prods = UsualSectionDumper("productions", "prods", "Productions")
	fragmented = UsualSectionDumper("fragmented", "fragmented", "Fragmented")
	keywords = UsualSectionDumper("keywords", "keywords", "Keywords")
	tokens = UsualSectionDumper("tokens", "tokens", "Tokens")
	chars = UsualSectionDumper("characters", "chars", "Characters")


class SectionedGeneratorContext(GeneratorContext):
	__slots__ = ("sections",)

	def __init__(self, currentProdName: typing.Optional[str], sections=None) -> None:
		super().__init__(currentProdName)
		if sections is None:
			sections = defaultdict(list)
		self.sections = sections

	def spawn(self) -> "SectionedGeneratorContext":
		return self.__class__(self.currentProdName, self.sections)


def doesDumperSupportContent(sectionDumper) -> bool:
	return isinstance(sectionDumper, SectionDumper) or (isinstance(sectionDumper, type) and issubclass(sectionDumper, SectionDumper))


class SectionedGenerator(UsualGenerator):
	__slots__ = ()
	DEFAULT_ORDER = ("prods", "fragmented", "keywords", "chars", "tokens")
	SECTIONER = Sectioner

	@classmethod
	def getOrder(cls, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		return cls.DEFAULT_ORDER

	@classmethod
	def initContext(cls, grammar: Grammar) -> SectionedGeneratorContext:
		return SectionedGeneratorContext(None)

	@classmethod
	def _transpile(cls, grammar: Grammar, ctx: typing.Any = None) -> typing.Iterable[str]:
		t = list(cls.SECTIONER.START(cls, grammar))

		cls.embedGrammar(grammar, ctx)

		for secName in cls.getOrder(grammar):
			sectionDumper = getattr(cls.SECTIONER, secName)
			if doesDumperSupportContent(sectionDumper):
				t.extend(sectionDumper.dumpSection(cls, grammar, ctx.sections[secName], ctx))
			else:
				t.extend(sectionDumper(cls, grammar, ctx))

		t.extend(cls.SECTIONER.END(cls, grammar))
		return t

	@classmethod
	def embedGrammar(cls, obj: Grammar, ctx: typing.Any = None) -> None:
		for secName in cls.getOrder(obj):
			sectionDumper = getattr(cls.SECTIONER, secName)
			if doesDumperSupportContent(sectionDumper):  # just class methods in SECTIONER can be used only in scope of a grammar file, they cannot be used when embedding other rules
				ctx.sections[secName].extend(tuple(sectionDumper.dumpContent(cls, obj, ctx)))
