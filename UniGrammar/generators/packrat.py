import typing
from pathlib import Path

from UniGrammarRuntimeCore.ICompiler import DummyCompiler

from ..core.backend.Runner import Runner
from ..core.CharClassProcessor import CharClassMergeProcessor
from UniGrammarRuntime.ToolMetadata import Product
from UniGrammarRuntime.dslsMetadata import packrat as packratDSLMeta
from .pythonicGenerator import PythonicGenerator


class PackratGenerator(PythonicGenerator):
	META = packratDSLMeta

	assignmentOperator = " = "
	singleLineCommentStart = "#"
	alternativesSeparator = " / "

	DEFAULT_ORDER = ("prods", "fragmented", "keywords", "chars", "tokens")

	class CHAR_CLASS_PROCESSOR(CharClassMergeProcessor):
		charClassSetStart = '~r"' + PythonicGenerator.CHAR_CLASS_PROCESSOR.charClassSetStart
		charClassSetEnd = PythonicGenerator.CHAR_CLASS_PROCESSOR.charClassSetEnd + '"'
