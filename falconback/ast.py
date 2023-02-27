"""
AST
---

Abstract syntax tree nodes.
"""

from collections import namedtuple

Number = namedtuple('Number', ['value'])
String = namedtuple('String', ['value'])
Identifier = namedtuple('Identifier', ['value'])
Assignment = namedtuple('Assignment', ['left', 'right'])
BinaryOperator = namedtuple('BinaryOperator', ['operator', 'left', 'right'])
UnaryOperator = namedtuple('UnaryOperator', ['operator', 'right'])
Call = namedtuple('Call', ['left', 'arguments', 'tagged'])
Function = namedtuple('Function', ['name', 'params', 'body', 'ret'])
Condition = namedtuple('Condition', ['test', 'if_body', 'elifs', 'else_body'])
ConditionElif = namedtuple('ConditionElif', ['test', 'body'])
Match = namedtuple('Match', ['test', 'patterns', 'else_body'])
MatchPattern = namedtuple('MatchPattern', ['pattern', 'body'])
WhileLoop = namedtuple('WhileLoop', ['test', 'body'])
ForLoop = namedtuple('ForLoop', ['var_name', 'collection', 'body'])
Break = namedtuple('Break', [])
Continue = namedtuple('Continue', [])
Return = namedtuple('Return', ['value'])
Array = namedtuple('Array', ['items'])
Dictionary = namedtuple('Dictionary', ['items'])
SubscriptOperator = namedtuple('SubscriptOperator', ['left', 'key'])
Program = namedtuple('Program', ['body'])
TypedName = namedtuple('TypedVariable', ['name', 'type', 'value'])
UsingNode = namedtuple("UsingNode", ['module'])
ClassDefinition = namedtuple('ClassDefinition',['name', 'parents', 'body'])
ClassAccess = namedtuple('ClassAccess', ['left', 'right'])
GroupExpression = namedtuple('GroupExpression', 'left')
TypedParam = namedtuple('TypedParam', ['name', 'data_type'])
Enum = namedtuple('Enum', ['name', 'items'])
Cpp = namedtuple('Cpp', ['statements'])
InferedName = namedtuple('InferedName', ['name', 'value'])
