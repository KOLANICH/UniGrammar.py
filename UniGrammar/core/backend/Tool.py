import typing


class ToolMeta(type):
	__slots__ = ()

	def __new__(cls: typing.Type["ToolMeta"], className: str, parents: typing.Tuple[typing.Type, ...], attrs: typing.Dict[str, typing.Any]) -> "Tool":  # pylint:disable=arguments-differ

		if parents:
			if "RUNNER" in attrs:
				runner = attrs["RUNNER"]
			else:
				runner = parents[0].RUNNER

			if runner:
				if attrs["GENERATOR"].META.product is None:
					attrs["GENERATOR"].META.product = runner.PARSER.META.product
			else:
				raise ValueError("RUNNER must be set!")

		return super().__new__(cls, className, parents, attrs)


class Tool(metaclass=ToolMeta):
	RUNNER = None
	GENERATOR = None
