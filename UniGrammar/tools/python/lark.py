import typing
from pathlib import Path
import inflection

from UniGrammarRuntime.backends.python.lark import LarkParserFactory, masterBranchURI
from UniGrammarRuntime.ParserBundle import InMemoryGrammarResources
from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from ...core.ast import Grammar, Productions
from ...core.ast.base import Name
from ...core.ast.characters import CharClass, CharClassUnion
from ...core.backend.Generator import TranspiledResult
from ...core.backend.Runner import Runner, NotYetImplementedRunner
from ...core.backend.SectionedGenerator import SectionedGenerator
from ...core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.grammarClasses import PEG
from UniGrammarRuntime.ToolMetadata import ToolMetadata, Product
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...utils.escapelib import CompositeEscaper, backslashUHexEscaper, closingSquareBracketEscaper, commonCharsEscaper, doubleTickEscaper
from ...generators.pythonicGenerator import PythonicGenerator

charClassEscaper = CompositeEscaper(commonCharsEscaper, closingSquareBracketEscaper, backslashUHexEscaper)


def transformNameForLark(k: str) -> str:
	"""Lark relies on case to determine rule type: terminals are whole uppercase, non-terminals are whole lowercase. This function transforms the names."""
	isTerminal = k[0].isupper()  # We use ANTLR convention that terminals first letters must be uppercase and it is verified when parsing from serialized representation
	k = inflection.underscore(k)
	if isTerminal:
		return k.upper()
	return k.lower()

class LarkRunner(NotYetImplementedRunner):
	__slots__ = ()

	COMPILER = DummyCompiler
	PARSER = LarkParserFactory

	def __init__(self):
		raise NotImplementedError()

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		raise NotImplementedError()



class Lark(Tool):
	RUNNER = LarkRunner
	class GENERATOR(PythonicGenerator):
		META = DSLMetadata(
			officialLibraryRepo=masterBranchURI + "/examples",
			grammarExtensions=("lark",),
		)
		escaper = charClassEscaper

		assignmentOperator = ": "
		endStatementOperator = ""
		singleLineCommentStart = "//"

		DEFAULT_ORDER = ("firstRule", "prods", "fragmented", "keywords", "chars", "tokens")

		class SECTIONER(PythonicGenerator.SECTIONER):
			@classmethod
			def firstRule(cls, backend: SectionedGenerator, gr: Grammar, ctx: typing.Any = None):
				if gr.meta:
					yield backend.resolve(Name("start", gr.prods.findFirstRule().name), gr, ctx)

		@classmethod
		def wrapLiteralString(cls, s: str) -> str:
			return '"' + doubleTickEscaper(s) + '"'

		@classmethod
		def Ref(cls, obj, grammar: typing.Optional[Grammar], ctx: typing.Any = None) -> str:
			return transformNameForLark(obj.name)

		@classmethod
		def _Name(cls, k: str, v: str, ctx: typing.Any = None) -> str:
			return super()._Name(transformNameForLark(k), v, ctx)
