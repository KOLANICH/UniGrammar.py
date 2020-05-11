import sre_parse
import sre_constants
import unicodedata
import warnings
from pprint import pprint

from ..core.backend.Lifter import *
from ..core.ast.base import *
from ..core.ast.characters import *
from ..core.ast.tokens import *
from ..core.ast.prods import *
from ..core.ast import *

from ..generators.UniGrammarDictGenerator import UniGrammarDictGenerator, transpileToSerialized
from .. import transpile
from transformerz.serialization.yaml import yamlSerializer


wellKnownRegExpRemap = {
	"CATEGORY_WORD": CharClassUnion(WellKnownChars("ascii_letters"), WellKnownChars("digits"), CharClass("_")),
	"CATEGORY_DIGIT": WellKnownChars("digits"),
	"CATEGORY_NOT_WORD": CharClassUnion(WellKnownChars("ascii_letters"), WellKnownChars("digits"), CharClass("_"), negative=True),
	"CATEGORY_NOT_DIGIT": WellKnownChars("digits", negative=True),
	"CATEGORY_SPACE": WellKnownChars("whitespace"),
	"CATEGORY_NOT_SPACE": WellKnownChars("whitespace", negative=True),
}

anyChar = CharClass("", negative=True)


class REVisitor:
	@classmethod
	def _preEach(cls, tp, args, ctx):
		if tp != sre_constants.LITERAL:
			cls.processCombinedLiterals(ctx)

	@classmethod
	def _post(cls, ctx):
		cls.processCombinedLiterals(ctx)

	@classmethod
	def processCombinedLiterals(cls, ctx):
		if ctx.prevStr:
			ctx.prevStr = "".join(ctx.prevStr)
			if len(ctx.prevStr) == 1:
				sect = ctx.chars
			else:
				sect = ctx.keywords
			sect[ctx.prevStr] = Lit(ctx.prevStr)
			ctx.prevStr = []

	def LITERAL(charCode: int, ctx=None):
		ctx.prevStr.append(chr(charCode))

	def ANY(reserved):
		ctx.chars["ANY"] = anyChar

	def IN(*args, ctx=None):
		cc = CharClass([])
		children = []
		negative = False
		loneChildName = None
		for ccType, ccArgs in args:
			if ccType == sre_constants.NEGATE:
				negative = True
			elif ccType == sre_constants.LITERAL:
				cc.chars.append(chr(ccArgs))
				loneChildName = unicodedata.name("a").replace(" ", "_").upper()
			elif ccType == sre_constants.CATEGORY:
				children.append(wellKnownRegExpRemap[ccArgs.name])
				loneChildName = "CHARS_" + ccArgs.name[6:]
			elif ccType == sre_constants.RANGE:
				children.append(CharRange(start=ccArgs[0], stop=ccArgs[1]))
				loneChildName = "CHARS_RANGE_" + str(ccArgs[0]) + "_" + str(ccArgs[1])
		if len(children) == 1:
			loneChild = children[0]
			loneChild.negative = negative
			if loneChildName is not None:
				name = loneChildName
			else:
				name = "CHARS_" + ccType.name + "_" + str(len(ctx.chars))
			ctx.chars[name] = loneChild
		else:
			ctx.chars["CHARS_UNION_" + str(len(ctx.chars))] = CharClassUnion(children, negative=negative)

	@classmethod
	def BRANCH(cls, unkn, alts, ctx=None):
		altRefs = []
		name = str("ALT_" + str(len(ctx.prods)))
		for i, subSeq in enumerate(alts):
			childName = name + "_VARIANT_" + str(i)
			newCtx = ctx.spawn(childName)
			cls.SUBPATTERN(childName, subSeq, newCtx)
			altRefs.append(Ref(newCtx.directInsertionOrder[-1].key))
		ctx.prods[name] = Alt(*altRefs)

	def GROUPREF(*args, ctx=None):
		raise ValueError("backrefs are completely not supported!")

	def AT(where, ctx=None):
		warnings.warn("AT opcode is ignored " + repr(where))
		#AT_BEGINNING_STRING \\A
		#AT_END_STRING \\Z

	def ASSERT_NOT(relativePosition, subSeq, ctx=None):
		raise ValueError("negative conditions are completely not supported!")

	@classmethod
	def MIN_REPEAT(cls, minCount, maxCount, iterArgs, ctx=None):
		"""Non-greedy matching"""
		warnings.warn("Non-greedy matching is not yet implemented, replacing with greedy one")
		cls.MAX_REPEAT(minCount, maxCount, iterArgs, ctx=ctx)

	@classmethod
	def MAX_REPEAT(cls, minCount, maxCount, iterArgs, ctx=None):
		nodeType = None
		assert len(iterArgs) == 1, "Strange iterArgs, IRL it is always of len 1: " + repr(iterArgs)

		newCtx = ctx.spawn("MAX_REPEAT " + repr((minCount, maxCount)))
		cls.SUBPATTERN(None, iterArgs, newCtx)
		subExprName = newCtx.directInsertionOrder[-1].key
		subExprRef = Ref(subExprName)
		childName = subExprName + "_iter"

		print("maxCount", maxCount, maxCount != sre_constants.MAXREPEAT)  # MAXREPEAT (without underscore) is for repeating indefinitely, MAX_REPEAT (with underscore) is opcode

		if maxCount != sre_constants.MAXREPEAT:
			biConstrainedSeq = []
			newCtx = ctx.spawn(childName)

			subExprOptRef = Opt(subExprRef)
			print(minCount, maxCount, maxCount - minCount)
			for i in range(minCount):
				newCtx.prods[childName + "_MAND_" + str(i)] = subExprRef
			for i in range(maxCount - minCount):
				newCtx.prods[childName + "_OPT_" + str(i)] = subExprOptRef

			postProcessSubExpr(childName, ctx, newCtx)
		else:
			ctx.prods[childName] = Iter(subExprRef, minCount)

	@classmethod
	def SUBPATTERN(cls, name, subSeq, ctx=None):
		newCtx = ctx.spawn("SUBPATTERN " + repr(name))

		for el in subSeq:
			tp = el[0]
			args = el[1]
			if not isinstance(args, (list, tuple)):
				args = (args,)

			REVisitor._preEach(tp, args, newCtx)

			#print("args", repr(args))
			getattr(REVisitor, tp.name)(*args, ctx=newCtx)

		REVisitor._post(newCtx)

		postProcessSubExpr(name, ctx, newCtx)


def postProcessSubExpr(name, ctx, newCtx):
	if name is None:
		name = "prod_" + str(len(ctx.prods))
	sect = ctx.prods

	print(ctx.label, "newCtx.directInsertionOrder", newCtx.directInsertionOrder)
	print(ctx.label, "newCtx.insertionOrder", newCtx.insertionOrder)
	if len(newCtx.directInsertionOrder) > 1:
		els = []
		for insAct in newCtx.directInsertionOrder:
			els.append(Ref(insAct.key))

		sect[name] = Seq(*els)
	elif len(newCtx.directInsertionOrder) == 1:
		ctx.directInsertionOrder.extend(newCtx.directInsertionOrder)
	else:
		raise Exception("Empty newCtx.directInsertionOrder, newCtx.label: " + newCtx.label)


class REConvertingContext(LiftingContext):
	__slots__ = ("prevStr",)

	def __init__(self, label=None):
		super().__init__(label)
		self.prevStr = []


class RELifter(Lifter):
	CONTEXT_TYPE = REConvertingContext

	def __call__(self, reText: str):
		grammar = Grammar(meta=GrammarMeta(iD=None, title="Generated from the regexp " + reText, licence=None, doc="This grammar was converted from a regexp " + reText, docRef=None, filenameRegExp=None), chars=Characters([]), keywords=Keywords([]), fragmented=Fragmented([]), tokens=Tokens([]), prods=Productions([]))
		ctx = self.__class__.CONTEXT_TYPE("root")
		parsedRe = sre_parse.parse(reText)
		print(reText)
		pprint(parsedRe)

		REVisitor.SUBPATTERN("main", parsedRe, ctx)

		for el in ctx.insertionOrder:
			getattr(grammar, el.sect.name).children.append(Name(el.key, el.element))


def convertToGrammar(reText: str):
	l = RELifter()
	return transpileToSerialized(grammar, UniGrammarDictGenerator, yamlSerializer)


if __name__ == "__main__":
	if len(argv) > 1:
		toConvert = argv[1]
	else:
		toConvert = "b\w{0,1}c"
	print(convertToGrammar(toConvert))
