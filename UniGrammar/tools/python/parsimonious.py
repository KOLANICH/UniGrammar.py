import typing
from pathlib import Path

from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from UniGrammarRuntime.backends.python.parsimonious import ParsimoniousParserFactory

from ...core.backend.Runner import Runner
from ...core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.grammarClasses import PEG
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ...generators.packrat import PackratGenerator


class ParsimoniousRunner(Runner):
	__slots__ = ("PG",)

	COMPILER = DummyCompiler
	PARSER = ParsimoniousParserFactory

	def __init__(self):
		from parsimonious.grammar import Grammar

		self.PG = Grammar

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		raise NotImplementedError()


class ParsimoniousGenerator(PackratGenerator):
	META = ParsimoniousParserFactory.FORMAT

	assignmentOperator = " = "
	singleLineCommentStart = "#"
	endStatementOperator = ""


class Parsimonious(Tool):
	RUNNER = ParsimoniousRunner
	GENERATOR = ParsimoniousGenerator
