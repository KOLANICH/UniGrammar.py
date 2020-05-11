from .base import Name, Wrapper
from .tokens import Seq


class Prefer(Wrapper):
	"""A preferrence for parser generators that allow to set them. Some grammars for some parser generators are impossible without them."""

	__slots__ = ("preference",)

	def __init__(self, child: Seq, preference: str) -> None:
		super().__init__(child)
		self.preference = preference


class Cap(Name):
	"""A name of a capture."""

	__slots__ = ()
