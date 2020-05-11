import typing
import ast

from ..ast.base import Node
from ..CodeGen import CodeGenContext


class WrapperGenContext(CodeGenContext):
	__slots_ = ("moduleMembers", "members", "currentProdName", "allBindings", "capToNameSchema", "itersProdNames")

	def __init__(self, currentProdName: typing.Optional[str], moduleMembers: typing.Iterable[typing.Union[ast.Import, ast.ImportFrom, ast.ClassDef]], members: typing.Iterable[ast.FunctionDef], allBindings: typing.Mapping[str, typing.Tuple[Node, Node]], capToNameSchema, itersProdNames) -> None:
		super().__init__(currentProdName)
		self.moduleMembers = moduleMembers
		self.members = members
		self.allBindings = allBindings
		self.capToNameSchema = capToNameSchema
		self.itersProdNames = itersProdNames

	def extendSchema(self, capName: str, refName: str, currentProdName: str = None):
		if currentProdName is None:
			currentProdName = self.currentProdName
		self.capToNameSchema[currentProdName][refName] = capName
