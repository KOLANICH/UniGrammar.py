import typing
import ast

from ..ast.base import Name, Ref, Wrapper
from ..ast.prods import Cap
from ..ast.templates import TemplateInstantiation
from ..ast.tokens import Opt, Seq

from .primitiveBlocks import astSelfArg
from .basicBlocks import genAssignStraight, genConstructAstObj, genFieldClass
from .primitiveSpecificBlocks import IParseResultAST
from .specificBlocks import getProcessorFuncNameForARef, getReturnTypeForARef, getReturnTypeForANode
from .WrapperFuncGen import WrapperFuncGen
from .WrapperGenContext import WrapperGenContext

WrapperGen = None  # initialized in __init__


class NotImplementedWrapperFuncGen(WrapperFuncGen):
	"""Wrapper function for these nodes is not needed."""

	__slots__ = ()

	def __call__(self, cls, obj: typing.Any, grammar: typing.Optional["Grammar"], ctx) -> typing.Any:
		raise NotImplementedError

	def getType(self, nodeOrName: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		raise NotImplementedError

	def getFuncName(self, refName: str):
		raise NotImplementedError


class NopWrapperFuncGen(WrapperFuncGen):
	"""Usually needed for modifiers not affecting AST"""
	__slots__ = ()

	def __call__(self, cls, obj: Wrapper, grammar: typing.Optional["Grammar"], ctx):
		return WrapperGen._processItem(obj.child, grammar, ctx)

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		return getReturnTypeForANode(node.child, ctx, refName)


class NameWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: Name, grammar: typing.Optional["Grammar"], ctx: None) -> str:
		return obj.name

	def getType(self, nodeOrName: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		raise NotImplementedError


class WrapperWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: Wrapper, grammar: typing.Optional["Grammar"], ctx):
		if isinstance(obj.child, Ref):
			processorFunc = getProcessorFuncNameForARef(obj.child.name, ctx)
			retType = getReturnTypeForARef(obj.child.name, ctx)
		else:
			raise NotImplementedError("For compatibility each suff that is `iter`ed must be a `ref`. Otherwise we are unable to process these grammars uniformly for all the supported backends. Please put content of `" + obj.name + "` into a separate rule")

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx, refName: str = None):
		return getReturnTypeForARef(node.child, ctx, refName)


class SeqWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: Seq, grammar: typing.Optional["Grammar"], ctx: WrapperGenContext) -> None:
		astObjClassName = ctx.currentProdName

		objName = "parsed"
		newOName = "rec"
		o = ast.Name(id=objName, ctx=ast.Load())
		astObjClassNameAST, to, ctor = genConstructAstObj(newOName, astObjClassName)
		body = [ctor]

		fields = []
		for f in obj.children:
			if isinstance(f, Cap):
				fields.append(f.name)
				if isinstance(f.child, Ref):
					ctx.extendSchema(f.name, f.child.name)
					processorFunc = getProcessorFuncNameForARef(f.child.name, ctx)
					retType = getReturnTypeForARef(f.child.name, ctx)
					body.append(genAssignStraight(to, f.name, processorFunc, o))
				else:
					raise NotImplementedError("For compatibility each suff that is captured must be a `ref`. Otherwise we are unable to process these grammars uniformly for all the supported backends. Please put content of `" + f.name + "` into a separate rule")

		ctx.moduleMembers.append(genFieldClass(astObjClassName, fields, bases=(IParseResultAST,)))

		body.append(ast.Return(value=ast.Name(newOName, ctx=ast.Load())))

		ctx.members.append(ast.FunctionDef(
			name="process_" + astObjClassName,
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
			returns=astObjClassNameAST,
			type_comment=None,
		))

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx: WrapperGenContext, refName: str = None) -> ast.Name:
		return ast.Name(refName, ctx=ast.Load())


class TemplateInstantiationWrapperFuncGen(WrapperFuncGen):
	__slots__ = ()

	def __call__(self, cls: typing.Type["WrapperGen"], obj: TemplateInstantiation, grammar: typing.Optional["Grammar"], ctx: WrapperGenContext) -> None:
		return ctx.members.extend(obj.template.transformWrapper(grammar, cls, ctx, **obj.params))

	def getType(self, node: typing.Union[Wrapper, Ref, str], ctx: WrapperGenContext, refName: str = None) -> ast.Subscript:
		return node.template.getReturnType(ctx, **node.params)

	def getFuncName(self, node: typing.Union[Wrapper, Ref, str], ctx: WrapperGenContext, refName: str = None) -> ast.Attribute:
		return node.template.getProcFunc(ctx, **node.params)
