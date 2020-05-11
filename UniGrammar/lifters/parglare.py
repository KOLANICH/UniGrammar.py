from pathlib import Path

import parglare
import ruamel.yaml
import pantarei
from ast import literal_eval

from UniGrammar.core.ast.base import *
from UniGrammar.core.ast.characters import *
from UniGrammar.core.ast.prods import *
from UniGrammar.core.ast import *

try:
	thisDir = Path(__file__).absolute().parent
except:
	thisDir = Path(".").absolute()

yaml = ruamel.yaml.YAML(typ="rt")

tests = yaml.load(thisDir / "tests.yaml")

g = parglare.Grammar.from_file(str(thisDir / "str.pg"))
g = parglare.Grammar.from_file(str(thisDir.parent / "basics/basics.pg"))


characters = Characters([])
keywords = Keywords([])
tokens = Tokens([])
fragmented = Fragmented([])
prods = Productions([])


def processSeq(r):
	seqItems = []
	isToken = True
	for s in r:
		isToken &= isinstance(s, parglare.grammar.Terminal)
		seqItems.append(Ref(s.fqn))
	return Seq(*seqItems), (tokens if isToken else prods)


def processAlt(ps):
	alts = []
	for p in ps:
		if len(p.rhs) > 1:
			raise ValueError("This production is incomaptible to Alt. Move Seq into a separate production.")
		elif len(p.rhs) < 1:
			raise ValueError("Empty production")
		alts.append(p.rhs[0])
	return Alt(*alts), prods


def processNonTerminal(s):
	dqstr.fqn
	dqstr.name
	if len(dqstr.productions) == 1:
		return processSeq(dqstr.productions[0]), prods
	else:
		return processAlt(dqstr.productions), prods


def processTerminal(r):
	#raise ValueError("Unknown parglare AST terminal node", s)
	if isinstance(r, parglare.grammar.StringRecognizer):
		if r.ignore_case:
			raise ValueError("UniGrammar doesn't support caseless matching yet")
		print(r.value, r.ignore_case)

		if len(r.value) == 1:
			sect = keywords
		else:
			sect = characters
		return CharClass(r.value, False), sect
	else:
		raise ValueError("Unknown parglare AST terminal node recognizer", r)


def convert():
	for id, s in g.symbols_by_name.items():
		#print(id, s)
		#s.prior
		#s.prefer

		if isinstance(s, parglare.grammar.NonTerminal):
			res, sect = processNonTerminal(s)
		elif isinstance(s, parglare.grammar.Terminal):
			res, sect = processTerminal(s.recognizer)
		else:
			raise ValueError("Unknown parglare AST node", s)

		if res:
			sect.children.append(res)

	meta = GrammarMeta("str")
	gr = Grammar(meta, None, characters=characters, prods=prods)
	_transpile()
