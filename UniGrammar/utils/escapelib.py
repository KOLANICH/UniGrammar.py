import typing
import re
import string
from abc import ABC, abstractmethod
from ast import literal_eval

from rangeslicetools.tree import RangesTree

from .charRanges import multiRSub, stringToRanges


def generateEscapeMapForRegExpCharClass() -> typing.Dict[int, str]:
	try:
		specialCharsMap = type(re._special_chars_map)(re._special_chars_map)  # pylint: disable=protected-access
		allowedChars = " *+|#~&(){}^[$?"
		for c in allowedChars:
			del specialCharsMap[ord(c)]
	except:
		specialCharsMap = {
			"\n": "\\n",
			"\r": "\\r",
			".": "\\.",
			0: "\\0",
			"]": "\\]"
		}
	return specialCharsMap


ourSpecialCharsMap = generateEscapeMapForRegExpCharClass()


def reCharClassEscape(c: str) -> str:
	c = repr(c)[1:-1]
	if len(c) == 1:
		c = c.translate(ourSpecialCharsMap)
	return c


def hexStringizer(x: int) -> str:
	return hex(x)[2:]


def backslashUHex4CodePointsStringizer(c: str) -> str:
	res = hexStringizer(c)
	threshold = 4
	res = "0" * (threshold - len(res)) + res
	return res


stringizers = {
	"hex": hexStringizer,
	"uhex": backslashUHex4CodePointsStringizer,
	"oct": lambda x: oct(x)[2:],
	"dec": str,
}


class CharEscaper(ABC):
	@abstractmethod
	def __call__(self, c: str) -> str:
		raise NotImplementedError()


def createDefaultCharsToEscape() -> RangesTree:
	visible = stringToRanges("".join(sorted(set(string.printable) - set(string.whitespace) | {" "})))
	invisible = tuple(multiRSub(visible, base=range(0, 0xFF)))
	return RangesTree.build(invisible)


defaultCharsToEscape = createDefaultCharsToEscape()


class UnicodeEscaper(CharEscaper):
	__slots__ = ("range", "template", "stringizer")

	def __init__(self, template: str, ranges: RangesTree = None, stringizer: str = "hex") -> None:
		self.template = template

		if ranges is None:
			ranges = defaultCharsToEscape

		self.range = ranges
		if isinstance(stringizer, str):
			stringizer = stringizers[stringizer]
		self.stringizer = stringizer

	def __call__(self, c: str) -> str:
		cc = ord(c)
		res = tuple(self.range[cc])
		if res:
			return self.template.format(self.stringizer(cc))
		return c


class CompositeEscaper(CharEscaper):
	__slots__ = ("children",)

	def __init__(self, *children) -> None:
		self.children = children

	def __call__(self, c: str) -> str:
		for e in self.children:
			c = e(c)
			if len(c) != 1:
				return c
		return c


def genRemappingEscapeCharsLiterally(s: str) -> typing.Dict[int, str]:
	return {ord(c): ("\\" + c) for c in s}


class RemappingEscaper(CharEscaper):
	__slots__ = ("mapping",)

	def __init__(self, mapping: typing.Union[str, typing.Dict[int, str]]) -> None:
		if isinstance(mapping, str):
			mapping = genRemappingEscapeCharsLiterally(mapping)
		self.mapping = mapping

	def __call__(self, c: str) -> str:
		return c.translate(self.mapping)


pythonRegExpEscaper = RemappingEscaper(ourSpecialCharsMap)


def genCommonRemapping() -> typing.Dict[int, str]:
	res = genRemappingEscapeCharsLiterally("\\")
	for cc in "abtrn":
		escSeq = "\\" + cc
		res[ord(literal_eval('"' + escSeq + '"'))] = escSeq
	return res


commonCharsEscaper = RemappingEscaper(genCommonRemapping())


class PythonReprEscaper(CharEscaper):
	__slots__ = ()

	def __call__(self, c: str) -> str:
		return repr(c)[1:-1]


class PythonREEscaper(CharEscaper):
	__slots__ = ()

	def __call__(self, c: str) -> str:
		return re.escape(c)


pythonReprEscaper = PythonReprEscaper()
pythonREEscaper = PythonREEscaper()

pythonRegexEscaper = CompositeEscaper(pythonReprEscaper, pythonREEscaper)


singleTickEscaper = RemappingEscaper("'")
doubleTickEscaper = RemappingEscaper('"')
closingSquareBracketEscaper = RemappingEscaper("]")
backslashUHexEscaper = UnicodeEscaper("\\u{{{}}}", stringizer="uhex")
backslashXHexEscaper = UnicodeEscaper("\\x{}", stringizer="hex")

commonEscaper = CompositeEscaper(commonCharsEscaper, backslashUHexEscaper)

defaultCharClassEscaper = CompositeEscaper(commonEscaper, closingSquareBracketEscaper)
defaultStringEscaper = CompositeEscaper(commonEscaper, doubleTickEscaper)
