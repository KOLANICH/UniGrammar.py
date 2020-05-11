import typing
from pathlib import Path

from antlrCompile import ANTLR as ANTLRCompileANTLR, Vis as ANTLRCompileVis

from UniGrammarRuntime.backends.multilanguage.antlr4 import ANTLRParser, ANTLRParserFactory, toolGithubOrg, languagesRemap
from UniGrammarRuntime.ParserBundle import InMemoryGrammarResources

from ...core.ast import Grammar, Spacer
from ...core.ast.characters import CharClass, CharClassUnion
from ...core.backend.Generator import TranspiledResult
from ...core.backend.Runner import Runner
from ...core.backend.SectionedGenerator import SectionedGenerator, Sectioner
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...utils.escapelib import CompositeEscaper, closingSquareBracketEscaper, commonEscaper, singleTickEscaper

ourCharClassEscaper = CompositeEscaper(commonEscaper, closingSquareBracketEscaper)
ourStringEscaper = CompositeEscaper(commonEscaper, singleTickEscaper)


class ANTLR(ANTLRCompileANTLR):
	__slots__ = ()

	def compileStr(self, grammarText: str, target:str = "python", fileName: typing.Optional[typing.Union[Path, str]] = None):
		return super().compileStr(grammarText, languagesRemap[target], fileName)



class ANTLRGenerator(SectionedGenerator):
	charClassEscaper = ourCharClassEscaper
	stringEscaper = ourStringEscaper

	META = DSLMetadata(
		officialLibraryRepo=toolGithubOrg + "/grammars-v4",
		grammarExtensions=("g4",),
	)

	assignmentOperator = ": "
	capturingOperator = "="
	endStatementOperator = ";"
	singleLineCommentStart = "//"

	DEFAULT_ORDER = ("prods", "fragmented", "keywords", "tokens", "chars")

	class SECTIONER(Sectioner):
		@classmethod
		def START(cls, backend: SectionedGenerator, gr: Grammar, ctx: typing.Any = None):
			yield from super(cls, cls).START(backend, gr, ctx)
			yield "grammar " + gr.meta.id + backend.endStatementOperator
			yield backend.resolve(Spacer(), gr, ctx)

	@classmethod
	def wrapLiteralString(cls, s: str) -> str:
		return "'" + cls.stringEscaper(s) + "'"

	#@classmethod
	#def wrapLiteralChar(cls, s: str) -> str:
	#	return

	@classmethod
	def wrapCharClass(cls, s: str, obj: typing.Union[CharClassUnion, CharClass], grammar: Grammar) -> str:
		res = "[" + s + "]"
		if obj.negative:
			res = "~" + res
		return res

class ANTLRRunner(Runner):
	__slots__ = ()

	COMPILER = ANTLR
	PARSER = ANTLRParserFactory

	def saveCompiled(self, internalRepr, grammarResources: InMemoryGrammarResources, meta: ToolMetadata, target: str="python"):
		for name, text in internalRepr.asFileNameDict().items():
			grammarResources.parent.backendsTextData[meta.product.name, name] = text

	def execute(self, res):
		return self.__class__.PARSER.fromCompResult(res)

	def parse(self, parser, text: str) -> None:
		return parser(text)

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		v = ANTLRCompileVis()
		window = v.treeGUIVisualization(parser, text, block=False)
		window.setTitle(window.getTitle() + " (from UniGrammar)")
		v.blockOnGUIWindow(window)


class ANTLR(Tool):
	RUNNER = ANTLRRunner
	GENERATOR = ANTLRGenerator
