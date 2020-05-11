import typing
from pathlib import Path

from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from UniGrammarRuntime.backends.python.parglare import ParglareParserFactory, toolGitRepo
from UniGrammarRuntime.ParserBundle import InMemoryGrammarResources

from ...core.ast import Comment, Grammar, Name, Spacer
from ...core.ast.characters import CharClass, CharClassUnion
from ...core.ast.tokens import Alt, Opt
from ...core.ast.prods import Prefer
from ...core.backend.Generator import Generator, TranspiledResult, GeneratorContext
from ...core.backend.Runner import Runner
from ...core.backend.SectionedGenerator import Sectioner
from UniGrammarRuntime.grammarClasses import GLR, LR
from UniGrammarRuntime.ToolMetadata import ToolMetadata, Product
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...generators.pythonicGenerator import PythonicGenerator


class ParglareRunner(Runner):
	__slots__ = ()

	COMPILER = DummyCompiler
	PARSER = ParglareParserFactory

	def compileAndSave(self, internalRepr, grammarResources: InMemoryGrammarResources, meta: ToolMetadata, target: str = "python"):
		super().compileAndSave(internalRepr, grammarResources, meta, target)
		"""TODO: create .pgt file
		from parglare.tables.persist import table_from_serializable, table_to_serializable
		p = parglare.grammar.get_grammar_parser(False, False)
		p.parse(grammarText.read_text())
		p.table
		"""

	def execute(self, g: typing.Any) -> typing.Any:
		return g

	def parse(self, parser: "parglare.parser.Parser", text: str) -> None:
		parser.parse(text)

	def trace(self, parser: "parglare.parser.Parser", text: str):
		raise NotImplementedError()
		#grammar_pda_export(table, "%s.dot" % gF)

	def visualize(self, parser: "parglare.parser.Parser", text: str):
		raise NotImplementedError()


class ParglareGenerator(PythonicGenerator):
	META = ParglareParserFactory.FORMAT

	assignmentOperator = ": "
	capturingOperator = "="
	endStatementOperator = ";"
	singleLineCommentStart = "//"
	emptyTerminalConstant = "EMPTY"

	CONTEXT_CLASS = GeneratorContext

	DEFAULT_ORDER = ("prods", "fragmented", "LAYOUT", "keywords", "tokens", "terminalsKeyword", "chars")

	class SECTIONER(Sectioner):
		@classmethod
		def LAYOUT(cls, backend: Generator, gr: Grammar, ctx: typing.Any = None):
			yield "LAYOUT: EMPTY;"

		@classmethod
		def terminalsKeyword(cls, backend: Generator, gr: Grammar, ctx: typing.Any = None):
			yield "terminals"

	@classmethod
	def Opt(cls, obj, grammar: Grammar, ctx: typing.Any = None) -> str:
		if len(ctx.stack) > 1 and isinstance(ctx.stack[-2], Prefer):
			ctx.stack.pop()  # replacing with Alt
			res = cls.resolve(Alt(obj.child, cls.emptyTerminalConstant), grammar, ctx)
			ctx.stack.append(obj)  # returning to its place
			return res
		return super().Opt(obj, grammar, ctx)

	@classmethod
	def _Prefer(cls, res: str, preference: str, grammar: Grammar) -> str:
		return cls._Seq([res, "{" + preference + "}"], grammar)


class Parglare(Tool):
	RUNNER = ParglareRunner
	GENERATOR = ParglareGenerator
