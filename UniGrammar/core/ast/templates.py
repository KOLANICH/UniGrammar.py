import typing

from .base import Node, Ref


class TemplateInstantiation(Node):
	__slots__ = ("template", "params",)

	def __init__(self, template: "Template", params: typing.Dict[str, Ref]) -> None:
		super().__init__()
		self.template = template
		self.params = params
