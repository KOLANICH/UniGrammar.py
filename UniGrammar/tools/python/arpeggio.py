import typing
from pathlib import Path

from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from UniGrammarRuntime.backends.python.arpeggio import ArpeggioParserFactory, toolGitRepo

from ...core.backend.Runner import Runner
from ...core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.grammarClasses import PEG
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...generators.packrat import PythonicGenerator, PackratGenerator


class ArpeggioRunner(Runner):
	__slots__ = ("ParserPEG",)

	COMPILER = DummyCompiler
	PARSER = ArpeggioParserFactory

	def __init__(self):
		from arpeggio.peg import ParserPEG
		self.ParserPEG = ParserPEG

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		raise NotImplementedError()


class ArpeggioGenerator(PackratGenerator):
	META = ArpeggioParserFactory.FORMAT

	assignmentOperator = " <- "
	singleLineCommentStart = "//"
	endStatementOperator = ";"

	class CHAR_CLASS_PROCESSOR(CharClassMergeProcessor):
		charClassSetStart = "r'" + PythonicGenerator.CHAR_CLASS_PROCESSOR.charClassSetStart
		charClassSetEnd = PythonicGenerator.CHAR_CLASS_PROCESSOR.charClassSetEnd + "'"

class Arpeggio(Tool):
	RUNNER = ArpeggioRunner
	GENERATOR = ArpeggioGenerator
