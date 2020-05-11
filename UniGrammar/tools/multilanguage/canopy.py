import typing
from pathlib import Path

from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from UniGrammarRuntime.backends.multilanguage.canopy import CanopyParserFactory

from ...core.backend.Runner import Runner
from ..core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.grammarClasses import PEG
from UniGrammarRuntime.ToolMetadata import Product, ToolMetadata
from UniGrammarRuntime.DSLMetadata import DSLMetadata
from ...core.backend.Tool import Tool
from ..generators.packrat import PackratGenerator


class CanopyRunner(Runner):
	__slots__ = ("PG",)

	COMPILER = DummyCompiler
	PARSER = CanopyParserFactory

	def __init__(self):
		from canopy.grammar import Grammar

		self.PG = Grammar

	def trace(self, parser, text: str):
		raise NotImplementedError()

	def visualize(self, parser, text: str):
		raise NotImplementedError()


class CanopyGenerator(PackratGenerator):
	META = DSLMetadata(
		officialLibraryRepo=None,
		grammarExtensions=None
	)

	assignmentOperator = " = "
	singleLineCommentStart = "#"


class Canopy(Tool):
	RUNNER = CanopyRunner
	GENERATOR = CanopyGenerator
