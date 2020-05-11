import typing
import ast

from ..ast import Characters, Fragmented, Keywords, Section, Tokens
from ..ast.base import Node, Ref, Wrapper

from .primitiveBlocks import strAST
from .primitiveSpecificBlocks import terminalNodeToStr, iterateCollectionAst, getSubTreeTextAST

WrapperGen = None  # set in WrapperGen.__init__


def genIterateListCall(listVar: ast.Attribute) -> ast.Call:
	return ast.Call(
		func=iterateCollectionAst,
		args=[listVar],
		keywords=[],
	)


def getRefNameAndNodeForARef(nodeOrName: typing.Union[Wrapper, Ref, str], ctx: "WrapperGenContext", refName: str = None) -> typing.Tuple[str, Node, Section]:
	if isinstance(nodeOrName, Ref):
		refName = nodeOrName.name
		node = None
	elif isinstance(nodeOrName, str):
		refName = nodeOrName
		node = None
	else:
		node = nodeOrName

	if refName is None:
		raise NotImplementedError("We need a separate production for this stuff.", nodeOrName)

	if node is None:
		node, section = ctx.allBindings[refName]

	return refName, node, section


def getProcessorFuncNameForANode(node, ctx, refName=None):
	nodeName = type(node).__name__
	funcGen = getattr(WrapperGen, nodeName, None)
	if funcGen is not None:
		return funcGen.getFuncName(node, ctx, refName)
	else:
		raise ValueError("Unsupported node", node)


def getProcessorFuncNameForARef(nodeOrName: typing.Union[Wrapper, Ref, str], ctx: "WrapperGenContext", refName: str = None) -> ast.Attribute:
	refName, node, section = getRefNameAndNodeForARef(nodeOrName, ctx, refName)

	if isinstance(section, (Characters, Keywords)):
		return terminalNodeToStr
	elif isinstance(section, (Fragmented, Tokens)):
		return getSubTreeTextAST
	else:
		return getProcessorFuncNameForANode(node, ctx, refName)


def getReturnTypeForANode(node, ctx, refName=None):
	nodeName = type(node).__name__
	funcGen = getattr(WrapperGen, nodeName, None)
	if funcGen is not None:
		return funcGen.getType(node, ctx, refName)
	else:
		raise ValueError("Unsupported node", node)


def getReturnTypeForARef(nodeOrName: typing.Union[Wrapper, Ref, str], ctx: "WrapperGenContext", refName: str = None) -> typing.Union[ast.Name, ast.Subscript]:
	refName, node, section = getRefNameAndNodeForARef(nodeOrName, ctx, refName)

	if isinstance(section, (Characters, Tokens, Keywords)):
		return strAST
	elif isinstance(section, Fragmented):
		return strAST
	else:
		return getReturnTypeForANode(node, ctx, refName)
