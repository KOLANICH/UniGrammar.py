import typing
from pathlib import Path

from UniGrammarRuntime.backends.python.TatSu import TatSuParserFactory, TatSuParserFactoryFromSource, toolGitRepo
from UniGrammarRuntime.ParserBundle import InMemoryGrammarResources

from ...core.ast import Grammar, Spacer
from ...core.backend.Generator import TranspiledResult
from ...core.backend.Runner import Runner
from ...core.backend.SectionedGenerator import Sectioner
from UniGrammarRuntime.grammarClasses import PEG
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...generators.pythonicGenerator import PythonicGenerator


class TatSuRunner(Runner):
	__slots__ = ()

	COMPILER = TatSuParserFactoryFromSource
	PARSER = TatSuParserFactory

	def trace(self, parser, text: str):
		raise NotImplementedError("Not yet implemented")

	def visualize(self, parser, text: str):
		raise NotImplementedError()

	def saveCompiled(self, internalRepr, grammarResources: InMemoryGrammarResources, meta: ToolMetadata, target: str = "python"):
		import tatsu
		grammarResources.parent.backendsTextData[meta.product.name, grammarResources.name + "." + meta.mainExtension] = tatsu.codegen.codegen(internalRepr, target=target)
		#grammarResources.parent.backendsTextData[meta.name, grammarResources.name + "." + meta.mainExtension] = internalRepr

	def compileAndSave(self, transpiledResult: TranspiledResult, grammarResources: InMemoryGrammarResources, target: typing.Optional[str]="python") -> None:
		import tatsu




class TatSuGenerator(PythonicGenerator):
	META = TatSuParserFactoryFromSource.FORMAT

	assignmentOperator = " = "
	capturingOperator = ":"
	endStatementOperator = ";"
	singleLineCommentStart = "#"
	DEFAULT_ORDER = ("prods", "fragmented", "keywords", "chars", "tokens")

	class SECTIONER(Sectioner):
		@classmethod
		def START(cls, backend: PythonicGenerator, gr: Grammar, ctx: typing.Any = None):
			yield from super(cls, cls).START(backend, gr)
			yield "@@grammar :: " + gr.meta.id
			yield "@@whitespace :: //"
			yield "@@left_recursion :: False"
			yield backend.resolve(Spacer(2), gr, ctx)

	@classmethod
	def wrapZeroOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "{" + res + "}*"

	@classmethod
	def wrapOneOrMore(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "{" + res + "}+"

	@classmethod
	def wrapZeroOrOne(cls, res: str, grammar: Grammar, ctx: typing.Any=None) -> str:
		return "[" + res + "]"


class TatSu(Tool):
	RUNNER = TatSuRunner
	GENERATOR = TatSuGenerator

