import typing
from pathlib import Path

from UniGrammarRuntime.backends.multilanguage.waxeye import WaxeyeParserFactory, masterBranchURI
from UniGrammarRuntime.ParserBundle import InMemoryGrammarResources
from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from ...core.ast import Grammar
from ...core.ast.characters import CharClass, CharClassUnion
from ...core.backend.Generator import TranspiledResult
from ...core.backend.Runner import Runner, NotYetImplementedRunner
from ...core.backend.SectionedGenerator import SectionedGenerator
from ...core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...utils.escapelib import CompositeEscaper, backslashUHexEscaper, closingSquareBracketEscaper, commonCharsEscaper

charClassEscaper = CompositeEscaper(commonCharsEscaper, closingSquareBracketEscaper, backslashUHexEscaper)


class WaxeyeRunner(NotYetImplementedRunner):
	__slots__ = ()

	COMPILER = DummyCompiler
	PARSER = WaxeyeParserFactory

	def __init__(self):
		raise NotImplementedError()

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		raise NotImplementedError()

"""
class WaxeyeRunner(Runner):
	__slots__ = ("waxeye",)

	COMPILER = None
	PARSER = WaxeyeParserFactory

	def __init__(self):
		import sh

		self.waxeye = sh.Command("./bin/waxeye")

	def compileAndSave(self, internalRepr, grammarResources: InMemoryGrammarResources, meta: ToolMetadata, target=None):
		raise NotImplementedError

	def trace(self, parser, text: str):
		raise NotImplementedError("Not yet implemented")

	def visualize(self, parser, text: str):
		raise NotImplementedError()
"""

class WaxeyeGenerator(SectionedGenerator):
	META = DSLMetadata(
		officialLibraryRepo=masterBranchURI + "/grammars",
		grammarExtensions=("waxeye",),
	)
	escaper = charClassEscaper

	assignmentOperator = " <- "
	endStatementOperator = ""
	singleLineCommentStart = "#"

	DEFAULT_ORDER = ("prods", "fragmented", "keywords", "chars", "tokens")

	class CHAR_CLASS_PROCESSOR(CharClassMergeProcessor):
		charClassSetStart = "["
		charClassSetEnd = "]"

		@classmethod
		def wrapNegativeOuter(cls, obj: typing.Union[CharClassUnion, CharClass], s) -> str:
			return ("!" if obj.negative else "") + s

		@classmethod
		def wrapNegativeInner(cls, obj: typing.Union[CharClassUnion, CharClass], s) -> str:
			return s

	@classmethod
	def wrapZeroOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "*" + res

	@classmethod
	def wrapOneOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "+" + res

	@classmethod
	def wrapZeroOrOne(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "?" + res


class Waxeye(Tool):
	GENERATOR = WaxeyeGenerator
	RUNNER = WaxeyeRunner
