import typing
import ast

from ..ast.base import Ref, Wrapper
from ..ast.prods import Cap
from ..ast.tokens import Alt, Opt
from .basicBlocks import genDirCall, genTypingUnion, unifiedGetAttr, genTypingOptional
from .primitiveBlocks import ASTNone, ASTTypeError, astSelfArg
from .specificBlocks import getProcessorFuncNameForARef, getReturnTypeForARef
from .WrapperFuncGen import WrapperFuncGen
from .WrapperGenContext import WrapperGenContext


def genAlternative(o: ast.Name, fieldName: str, processerFunc: ast.Attribute) -> typing.Iterator[typing.Union[ast.Assign, ast.If]]:
	fe = ast.Name(id=fieldName, ctx=ast.Load())
	yield ast.Assign(
		targets=[ast.Name(id=fieldName, ctx=ast.Store())],
		value=unifiedGetAttr(o, fieldName),
		type_comment=None,
	)
	yield ast.If(
		test=ast.Compare(left=fe, ops=[ast.IsNot()], comparators=[ASTNone]),
		body=[
			ast.Return(
				value=ast.Call(
					func=processerFunc,
					args=[fe],
					keywords=[],
				)
			)
		],
		orelse=[],
	)


def genNoAltMatchedRaise(o: ast.Name) -> ast.Raise:
	return ast.Raise(exc=ast.Call(func=ASTTypeError, args=[genDirCall(o)], keywords=[]), cause=None)


class AltWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: Alt, grammar: typing.Optional["Grammar"], ctx: WrapperGenContext) -> None:
		body = []
		objName = "parsed"
		o = ast.Name(id=objName, ctx=ast.Load())

		returnTypes = []

		objIsAlt = isinstance(obj, Alt)

		for alt in obj.children:
			if isinstance(alt, Cap):
				if isinstance(alt.child, Ref):
					ctx.extendSchema(alt.name, alt.child.name)
					processorFunc = getProcessorFuncNameForARef(alt.child.name, ctx)
					retType = getReturnTypeForARef(alt.child.name, ctx)
					body.extend(genAlternative(o, alt.name, processorFunc))
					returnTypes.append(retType)
				else:
					raise NotImplementedError("For compatibility each suff that is `alt`ed must be a `ref`. Otherwise we are unable to process these grammars uniformly for all the supported backends. Please put content of " + ("`" + alt.name if hasattr(alt, "name") else "the `opt` struct in `" + ctx.currentProdName) + "` into a separate rule")
			#else:
			#	raise NotImplementedError("Content of `" + repr(obj) + "` must be `cap`tured in order to allow detection of its presence")

		body.append(genNoAltMatchedRaise(o))

		if returnTypes:
			ctx.members.append(ast.FunctionDef(
				name="process_" + ctx.currentProdName,
				args=ast.arguments(
					posonlyargs=[],
					args=[astSelfArg, ast.arg(arg=objName, annotation=None, type_comment=None)],
					vararg=None,
					kwonlyargs=[],
					kw_defaults=[],
					kwarg=None,
					defaults=[],
				),
				body=body,
				decorator_list=[],
				returns=genTypingUnion(returnTypes),
				type_comment=None,
			))


	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx: WrapperGenContext, refName: str = None) -> ast.Subscript:
		return genTypingUnion(getReturnTypeForARef(alt.child, ctx) for alt in node.children if isinstance(alt, Cap))


class OptWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls, obj: Opt, grammar: typing.Optional["Grammar"], ctx):
		body = []
		objName = "parsed"
		o = ast.Name(id=objName, ctx=ast.Load())

		returnTypes = []

		objIsAlt = isinstance(obj, Alt)

		if isinstance(obj.child, Ref):
			processerFunc = getProcessorFuncNameForARef(obj.child.name, ctx)
			retType = getReturnTypeForARef(obj.child.name, ctx)
			fe = ast.Name(id=objName, ctx=ast.Load())
			body.append(ast.If(
				test=ast.Compare(left=fe, ops=[ast.IsNot()], comparators=[ASTNone]),
				body=[
					ast.Return(
						value=ast.Call(
							func=processerFunc,
							args=[fe],
							keywords=[],
						)
					)
				],
				orelse=[],
			))

			returnTypes.append(retType)
		else:
			raise NotImplementedError("For compatibility each suff that is `opt`ed must be a `ref`. Otherwise we are unable to process these grammars uniformly for all the supported backends. Please put content of " + ("`" + obj.name if hasattr(obj, "name") else "the `opt` struct in `" + ctx.currentProdName) + "` into a separate rule")

		ctx.members.append(ast.FunctionDef(
			name="process_" + ctx.currentProdName,
			args=ast.arguments(
				posonlyargs=[],
				args=[astSelfArg, ast.arg(arg=objName, annotation=None, type_comment=None)],
				vararg=None,
				kwonlyargs=[],
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=body,
			decorator_list=[],
			returns=genTypingOptional(retType),
			type_comment=None,
		))

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		return genTypingOptional(getReturnTypeForARef(node.child, ctx))

