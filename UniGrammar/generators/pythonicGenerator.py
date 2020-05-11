import typing

from ..core.ast import Grammar
from ..core.ast.characters import _CharClass, CharRange
from ..core.backend.SectionedGenerator import SectionedGenerator
from ..core.CharClassProcessor import CharClassMergeProcessor
from ..utils.escapelib import pythonRegexEscaper


class PythonicGenerator(SectionedGenerator):
	charClassEscaper = pythonRegexEscaper

	class CHAR_CLASS_PROCESSOR(CharClassMergeProcessor):
		charClassSetStart = "["
		charClassSetEnd = "]"

		@classmethod
		def encloseCharClass(cls, s: str, obj: _CharClass, grammar: Grammar) -> str:
			return "/" + cls.charClassSetStart + s.replace("/", r"\/") + cls.charClassSetEnd + "/"

	@classmethod
	def wrapLiteralString(cls, s: str) -> str:
		return repr(s)
