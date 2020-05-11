import ast

from ..defaults import mainParserVarName, runtimeWrapperInterfaceName, runtimeParserResultBaseName, mainProductionName
from .primitiveBlocks import ASTSelf

IWrapperAST = ast.Name(id=runtimeWrapperInterfaceName, ctx=ast.Load())
IParseResultAST = ast.Name(id=runtimeParserResultBaseName, ctx=ast.Load())
backendAST = ast.Attribute(value=ASTSelf, attr="backend", ctx=ast.Load())
mainProductionNameAttrAST = ast.Attribute(value=ASTSelf, attr=mainProductionName, ctx=ast.Load())
mainProductionNameNameAST = ast.Name(id=mainProductionName, ctx=ast.Store())
getSubTreeTextAST = ast.Attribute(value=backendAST, attr="getSubTreeText", ctx=ast.Load())
terminalNodeToStr = ast.Attribute(value=backendAST, attr="terminalNodeToStr", ctx=ast.Load())
iterateCollectionAst = ast.Attribute(value=backendAST, attr="iterateCollection", ctx=ast.Load())
backendParseAst = ast.Attribute(value=backendAST, attr="parse", ctx=ast.Load())
backendPreprocessASTAst = ast.Attribute(value=backendAST, attr="preprocessAST", ctx=ast.Load())
mainParserVarNameAST = ast.Name(id=mainParserVarName, ctx=ast.Store())
