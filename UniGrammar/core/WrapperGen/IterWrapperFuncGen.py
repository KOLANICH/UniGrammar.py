import typing
import ast

from ..ast.base import Ref, Wrapper
from ..ast.tokens import Iter
from .basicBlocks import genTypingIterable
from .primitiveBlocks import ASTSelf, astSelfArg
from .restWrapperFuncGens import WrapperWrapperFuncGen
from .specificBlocks import genIterateListCall, getProcessorFuncNameForARef, getReturnTypeForARef
from .WrapperGenContext import WrapperGenContext


def genIterateCollectionLoop(listVar: ast.Attribute, iterVarName: str, yieldBody: ast.Attribute) -> ast.For:
	res = ast.For(
		target=ast.Name(id=iterVarName, ctx=ast.Store()),
		iter=genIterateListCall(listVar),
		body=[
			ast.Expr(
				value=ast.Yield(
					value=yieldBody
				)
			)
		],
		orelse=[],
		type_comment=None,
	)
	return res


def genProcessCollectionToList(funcName: str, parentName: str, iterFuncName: str, processorFunc: ast.Attribute, firstArgName: str = "parsed", iterVarName: str = "f", returnType: None = None) -> typing.Iterator[ast.FunctionDef]:
	"""Generates a function transforming a collection (`min`) or a macro around it into a python `list` of nodes"""

	o = ast.Name(id=firstArgName, ctx=ast.Load())
	yield ast.FunctionDef(
		name=funcName,
		args=ast.arguments(
			posonlyargs=[],
			args=[
				astSelfArg,
				ast.arg(arg=firstArgName, annotation=None, type_comment=None),
			],
			vararg=None,
			kwonlyargs=[],
			kw_defaults=[],
			kwarg=None,
			defaults=[],
		),
		body=[
			ast.Return(
				value=ast.ListComp(
					elt=ast.Call(
						func=processorFunc,
						args=[ast.Name(id=iterVarName)],
						keywords=[],
					),
					generators=[
						ast.comprehension(target=ast.Name(id=iterVarName), iter=ast.Call(func=ast.Attribute(value=ASTSelf, attr=iterFuncName, ctx=ast.Load()), args=[o], keywords=[]), ifs=[], is_async=0)
					],
				)
			)
		],
		decorator_list=[],
		returns=(genTypingIterable(returnType) if returnType else None),
		type_comment=None,
	)


def genProcessCollection(propName, processorFunc, returnType, parentName="rec"):
	funcName = "process_" + propName
	iterFuncName = funcName + "_"
	firstArgName = "parsed"
	iterVarName = "f"

	o = ast.Name(id=firstArgName, ctx=ast.Load())

	funcDef = ast.FunctionDef(
		name=iterFuncName,
		args=ast.arguments(
			posonlyargs=[],
			args=[astSelfArg, ast.arg(arg=firstArgName, annotation=None, type_comment=None)],
			vararg=None,
			kwonlyargs=[],
			kw_defaults=[],
			kwarg=None,
			defaults=[],
		),
		body=[
			genIterateCollectionLoop(
				o,
				iterVarName,
				ast.Name(id=iterVarName, ctx=ast.Load())
			)
		],
		decorator_list=[],
		returns=(genTypingIterable(returnType) if returnType else None),
		type_comment=None,
	)
	yield funcDef
	yield from genProcessCollectionToList(funcName, parentName, iterFuncName, processorFunc)


class IterWrapperFuncGen(WrapperWrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: Iter, grammar: typing.Optional["Grammar"], ctx: WrapperGenContext):
		ctx.itersProdNames.add(ctx.currentProdName)
		if isinstance(obj.child, Ref):
			processorFunc = getProcessorFuncNameForARef(obj.child.name, ctx)
			retType = getReturnTypeForARef(obj.child.name, ctx)
			ctx.members.extend(genProcessCollection(ctx.currentProdName, processorFunc, retType))
		else:
			raise NotImplementedError("For compatibility each suff that is `iter`ed must be a `ref`. Otherwise we are unable to process these grammars uniformly for all the supported backends. Please put content of `" + obj.name + "` into a separate rule")

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		return genTypingIterable(super().getType(node, ctx, refName))
