"""
Interpreter
-----------

AST-walking interpreter.
"""
from __future__ import print_function
from cgitb import reset
import operator
from collections import namedtuple
from pydoc import classname
import re
from textwrap import indent
from falconback import ast
from falconback.lexer import Lexer, TokenStream
from falconback.parser import Parser
from falconback.errors import AbrvalgSyntaxError, report_syntax_error, AbrvalgCompileTimeError, AbrvalgInternalError
from falconback.utils import print_ast, print_tokens, print_env
from falconback.ops import add, sub, div, mul, mod,gt,ge,lt,le,eq,ne



BuiltinFunction = namedtuple('BuiltinFunction', ['params', 'body'])

class Break(Exception):
    pass


class Continue(Exception):
    pass


class Return(Exception):
    def __init__(self, value):
        self.value = value


class Environment(object):

    def __init__(self, parent=None, args=None):
        self._parent = parent
        self._values = {}
        self.lexer = None
        if args is not None:
            self._from_dict(args)

    def _from_dict(self, args):
        for key, value in args.items():
            self.set(key, value)

    def set(self, key, val):
        self._values[key] = val

    def get(self, key):
        val = self._values.get(key, None)
        if val is None and self._parent is not None:
            return self._parent.get(key)
        else:
            return val

    def asdict(self):
        return self._values

    def __repr__(self):
        return 'Environment({})'.format(str(self._values))

class_table = Environment()


def eval_type(eval, tps):
    
    for tp in tps:
        if type(eval) == tp:
            return tp(eval)
    
def eval_binary_operator(node, env):
    simple_operations = {
        '+': add,
        '-': sub,
        '*': mul,
        '/': div,
        '%': mod,
        '>': gt,
        '>=': ge,
        '<': lt,
        '<=': le,
        '==': eq,
        '!=': ne,
        '..': lambda start, end: ast.BinaryOperator('..', start, end),
        '...': lambda start, end: range(start, end + 1),
    }
    lazy_operations = {
        '&&': lambda lnode, lenv: eval_expression(lnode.left, lenv) + " && "+  eval_expression(lnode.right, lenv),
        '||': lambda lnode, lenv: eval_expression(lnode.left, lenv) + " || "+  eval_expression(lnode.right, lenv)
    }
    if node.operator in simple_operations:
        return simple_operations[node.operator](eval_expression(node.left, env), eval_expression(node.right, env))
    elif node.operator in lazy_operations:
        return lazy_operations[node.operator](node, env)
    else:
        raise Exception('Invalid operator {}'.format(node.operator))


def eval_unary_operator(node, env):
    operations = {
        '-': operator.neg,
        '!': operator.not_,
    }
    return operations[node.operator](eval_expression(node.right, env))


def eval_assignment(node, env):
    if isinstance(node.left, ast.SubscriptOperator):
        return eval_setitem(node, env)
    
    elif isinstance(node.left, ast.ClassAccess):
        name_token = node.left.left.value 
        access_name_token = node.left.right.value

        name = name_token.value
        line = name_token.line
        column = name_token.column 

        access_name = access_name_token.value   
        access_line = access_name_token.line 
        access_column = access_name_token.column + 1

        ret = eval_expression(node.right, env)

        found = False
        var = env.get(name)

        if var != None:
            if isinstance(var, ast.Call):
                err = AbrvalgInternalError('Static method and member access is not ready yet! sorry :)', access_line, access_column)
                report_syntax_error(env.lexer, err, len(access_name))

            var_type = var.type.value
            var_type_line = var.type.line
            var_type_column = var.type.column

            if var_type in class_table.asdict():
                class_members = class_table.get(var_type)
                for member in class_members:
                    if isinstance(member, ast.TypedName):
                            member_name = member.name.value
                            if member_name == access_name:
                                return "{}.{} = {};".format(name, access_name, eval_expression(node.right, env))
                
                err = AbrvalgCompileTimeError('Attempt to access an invalid class method or field', access_line, access_column)
                report_syntax_error(env.lexer, err, len(access_name))
    
    else:
        val = str(eval_expression(node.right, env))
        name_token = node.left.value
        var_name = name_token.value
        line = name_token.line
        column = name_token.column

        if env.get(var_name) == None:
            err = AbrvalgCompileTimeError('Variable is not defined', line, column)
            report_syntax_error(env.lexer, err, len(var_name))
        return "{} = {};".format(var_name, val)


def eval_condition(node, env):
    cond  = eval_expression(node.test, env)

    ret_str = " if (" + cond + ") {"
    _if_body = eval_statements(node.if_body, env) 
    ret_str += _if_body + "\n}"

    for cond in node.elifs:
        cnd = eval_expression(cond.test, env)
        ret_str += " else if (" + cnd + ") {"
        else_if_body = eval_statements(cond.body, env)
        ret_str += else_if_body + "\n}"

    if node.else_body is not None:
        ret_str += " else {"
        val = eval_statements(node.else_body, env)
        ret_str += val + "\n}"

    return ret_str


def eval_match(node, env):
    test = eval_expression(node.test, env)
    ret_str = "switch (" + test + ") {\n"
    for pattern in node.patterns:
        #if eval_expression(pattern.pattern, env) == test:
        #    return eval_statements(pattern.body, env)
        body = eval_statements(pattern.body, env)
        match = eval_expression(pattern.pattern, env)
        ret_str += "case " + match + ":\n{" + body + "\nbreak;\n}\n"
    if node.else_body is not None:
        default = eval_statements(node.else_body, env)
        ret_str += " default:\n{" + default + "\n}\n"
    ret_str += "}\n"

    return ret_str


def eval_while_loop(node, env):
    cond = eval_expression(node.test, env)
    body = eval_statements(node.body, env)

    ret_str = 'while (' + cond + ') {'
    ret_str += body + '\n}\n'
    return ret_str


def eval_for_loop(node, env):
    var_name = node.var_name
    env.set(var_name,0)
    collection = eval_expression(node.collection, env)

    ret_str = 'for '

    if isinstance(collection, ast.BinaryOperator):
        if collection.operator == '..':
            left= collection.left, 
            right = collection.right
            left = str(left[0])
            right = str(right)

            ret_str += '( auto ' + var_name + ': range::range(' + left + "," + right + ')) {' #+ " + 1"
            #ret_str += '; ' + var_name 
            body = eval_statements(node.body, env) 
            ret_str += body + "\n}"
        else:
            print("Syntax error: Invalid loop operator "+ collection.operator)
            exit()
    elif isinstance(collection, str):
        ret_str += "(auto {}: {}) ".format(var_name, collection) + "{"
        ret_str += eval_statements(node.body, env) + "\n}"

    return ret_str


def eval_function_declaration(node, env):
    name_token = node.name
    func_name = name_token.value
    func_line = name_token.line
    func_column = name_token.column 

    env.set(func_name, node)

    if node.ret != None:
        func = node.ret[1]
    else:
        func = "auto"
    
    if node.name == "main":
        params = node.params + [ast.TypedParam("argc", "i32"), ast.TypedParam("argv", "char**")]
        if node.ret != None:
            func = node.ret[1]
        else:
            func = "void"
    else:
        if node.ret != None:
            func = node.ret[1]
        else:
            func = "auto"
        params = node.params

    func = func + " " + func_name + "(" 
    call_env = Environment(env, None)
    call_env.lexer = env.lexer 

    for i in range(0, len(params)):
        param = params[i]
        if type(param) == ast.TypedParam:
            param_name_token = param.name
            param_type_token = param.data_type

            param_name = param_name_token.value
            param_line = param_name_token.line
            param_name_colum = param_name_token.column 

            param_type = param_type_token.value
            param_type_colum = param_type_token.column 

            func = func + param_type + " " + param_name  

            if call_env.get(param_name) != None:
                err = AbrvalgCompileTimeError('Redefinition of parameter not allowed', param_line, param_name_colum)
                report_syntax_error(env.lexer, err, len(param_name))

            call_env.set(param_name, 0)
        else:
            name = param.value
            line = param.line 
            column = param.column 

            if call_env.get(name) != None:
                err = AbrvalgCompileTimeError('Redefinition of parameter not allowed', line, column)
                report_syntax_error(env.lexer, err, len(name))
            call_env.set(name, 0)
            func = func + "auto " + name 


        if i != len(params) -1:
            func = func + ", "

    func = func + ") {"
    res = None
    try:
        res = eval_statements(node.body, call_env)
        func = func + str(res) + "\n}\n" 
    except Return as ret:
        return ret.value

    env.set(func_name, node)   
    return func

def eval_group(node, env):
    ret = "(" + eval_expression(node.left, env) + ")"
    return ret

def eval_auto_var(node, env):
    name_token = node.name 
    name = name_token.value
    line = name_token.line
    column = name_token.column 

    if env.get(name) != None:
        err = AbrvalgCompileTimeError('Variable is already defined', line, column)
        report_syntax_error(env.lexer, err, len(name))

    env.set(name, node)
    value = eval_expression(node.value, env)
    return "auto {} = {};".format(name, value)

def eval_cpp(node, env):
    ret = ""
    for statemts in node.statements:
        ret += "{}\n".format(statemts.value)
    
    return ret

def eval_enum(node, env):
    name_obj = node.name
    name = name_obj.value
    line = name_obj.line
    column = name_obj.column 

    items = node.items

    str = 'enum %s\n{\n' % (name)
    for item in items:
        n = item.value
        str = str + n  + ',\n'
        env.set(n, item)
    str = str + "};\n"

    return str
    

def eval_classaccess(node, env):
    ret_str = ""
    class_token = node.left.value
    name = class_token.value
    line = class_token.line
    column = class_token.column 

    is_obj = False
    is_class = False
    if env.get(name) == None:
        if class_table.get(name) == None:
            err = AbrvalgCompileTimeError('Attempt to access a member of a non existing class', line, column)
            report_syntax_error(env.lexer, err, len(name))
        else:
            is_class = True
    else:
        is_obj = True

    res = ""
    if type(node.right) == ast.Call:
        res = eval_call(node.right, env)
    elif type(node.right) == ast.Identifier :
        res = eval_expression(node.right, env)
    elif type(node.right) == ast.BinaryOperator:
        res = eval_expression(node.right, env)
        #TODO: fix codegen for obj::
        
    if is_class != None:
        ret_str += name +'.'
    else:
        ret_str += name +'().'

    ret_str += res

    return ret_str


def eval_classdef(node, env):
    class_name_token = node.name
    name = class_name_token.value
    line = class_name_token.line
    column = class_name_token.column
    ret_str = 'class ' + name

    if class_table.get(name) != None:
        err = AbrvalgCompileTimeError('Class is already defined', line, column)
        report_syntax_error(env.lexer, err, len(name))

    ret_str += ": public FalconBase"

    for i in range(0,len(node.parents)):
        parent_token = node.parents[i] 
        parent_name = parent_token.value
        parent_line = parent_token.line 
        parent_column = parent_token.column

        if class_table.get(parent_name) == None:
            err = AbrvalgCompileTimeError('Attempt to inherit a non-existing class', parent_line, parent_column)
            report_syntax_error(env.lexer, err, len(parent_name))

        elif i < len(node.parents) - 1:
            ret_str += ", public " + parent_name
        else:
            ret_str += parent_name 

    ret_str += " {\npublic:\n"
    body = ""
    params = []
    methods = []
    for stmt in node.body:
        if isinstance(stmt, ast.TypedName):
            name_token = stmt.name
            var_name = name_token.value
            line = name_token.line 
            column = name_token.column 

            type_token = stmt.type
            
            if stmt.value != None:
                err = AbrvalgCompileTimeError('Variable assignment is not permitted outside of methods', line, column)
                report_syntax_error(env.lexer, err, len(var_name))
            methods.append(stmt)
            pr = eval_typed_var(stmt, env)
            ret_str += pr + "\n"
            params.append((name_token, type_token))

        elif isinstance(stmt, ast.Assignment):
            token = stmt.left.value
            var_name = token.value
            line = token.line
            column = token.column 
            err = AbrvalgCompileTimeError('Type inferance is not permitted outside class methods', line, column)
            report_syntax_error(env.lexer, err, len(var_name))

        elif isinstance(stmt, ast.Function):
            methods.append(stmt)
            pr = eval_statement(stmt, env)
            ret_str += pr

        else:
            pr = eval_statement(stmt, env)
            ret_str += pr

    cons = ""
    stmt = ""
    __class__ = "\"{}(\" + ".format(name)
    for index in range(0, len(params)):
        name_token, type_token = params[index]

        stmt = stmt + "\nthis->" + name_token.value + " = " + name_token.value + ";"
        
        if index < len(params) - 1:
            __class__ += "this->{} + \",\" + ".format(name_token.value)
            cons = cons + " " + type_token.value + " " + name_token.value + ","
        else:
            cons = cons + " " + type_token.value + " " + name_token.value
            __class__ += "this->{} + \")\"".format(name_token.value)
        

    
    ret_str += "{}({})".format(name, cons) + "{\n" + "{}\n\n ".format(stmt) + "}\n"
    ret_str += "{}()".format(name) + "{}\n"
    ret_str += "~" +name + "() {}\n"

    ret_str += body + "\n};\n"
    class_table.set(name, methods)
    env.set(name, ast.Call(name, params, None))
    return ret_str

def eval_include(node, env):
    module = node.module
    #env.set(module, 0)
    return "#include <" + module + ".h>" 


def eval_typed_var(node, env):
    var_name_token = node.name
    var_type_token = node.type 

    var_line = var_name_token.line
    var_column = var_name_token.column 
    var_name = var_name_token.value

    var_type_column = var_type_token.column
    var_type = var_type_token.value

    ret_str = var_type + " " + var_name
    
    if env.get(var_name) != None:
        err = AbrvalgCompileTimeError("Variable is already defined", var_line, var_column)
        report_syntax_error(env.lexer, err, len(var_name))
    else:
        env.set(var_name, node)
    val = ""
    if node.value != None:
        val = " = " + str(eval_expression(node.value, env))
    ret_str += val + ";"
    return ret_str

def eval_call(node, env):
    function_token = node.left.value
    function_name = function_token.value
    function_line = function_token.line
    function_column = function_token.column

    if env.get(function_name) == None:
        err = AbrvalgCompileTimeError("Attempt to call an undefined function or procedure", function_line, function_column)
        report_syntax_error(env.lexer, err, len(function_name))

    if not isinstance(env.get(function_name), ast.Function):
        if not isinstance(env.get(function_name), ast.Call):
            print(env.get(function_name))
            err = AbrvalgCompileTimeError("Attempt to call a symbol without a function signature", function_line, function_column) 
            report_syntax_error(env.lexer, err, len(function_name))

    fx = env.get(function_name)
    ret_str = function_name + " ("

    n_actual_args = len(node.arguments)
    if isinstance(fx, ast.Call):
        expected_args = len(fx.arguments)
    else:
        expected_args = len(fx.params)


    if n_actual_args != expected_args:
        message = "Call to function expected {} parameters but received {} parameteres".format(expected_args, n_actual_args)
        err = AbrvalgCompileTimeError(message, function_line, function_column)
        report_syntax_error(env.lexer, err, len(function_name))


    for i in range(0, n_actual_args):
        param = node.arguments[i]

        val = ""
        
        if type(param) == ast.BinaryOperator:
            val = str(eval_expression(param, env))
        elif type(param) == ast.ClassAccess:
            val = "(" + str(eval_classaccess(param, env)) + ")"
        elif type(param) == ast.String:
            val = 'string("' + param.value + '")'
        elif type(param) == ast.Call:
            val = eval_call(param, env)
        elif type(param) == ast.SubscriptOperator:
            val = str(eval_expression(param, env))
        else:
            val = eval_expression(param, env)

        if i != n_actual_args -1:
            ret_str += val + " , "
        else:
            ret_str += val 
        
    if node.tagged == None:
        return ret_str + ");"
    else:
        return ret_str + ") "

def eval_identifier(node, env):
    token = node.value
    name = token.value
    line = token.line
    column = token.column

    val = env.get(name)
    if val is None:
        err = AbrvalgCompileTimeError("Variable is not defined", line, column)
        report_syntax_error(env.lexer, err, len(name))
    return name


def eval_getitem(node, env):
    #print(node)
    collection = eval_expression(node.left, env)
    key = eval_expression(node.key, env)
    return collection + '[' + key + ']'


def eval_setitem(node, env):
    collection = eval_expression(node.left.left, env)
    key = eval_expression(node.left.key, env)
    val = eval_expression(node.right, env)

    return collection + '.at(' + key + ') = ' + val + ';'


def eval_array(node, env):
    ret_str = "std::vector {"
    for i  in range(0, len(node.items)):
        item = node.items[i]
        val = eval_expression(item, env) 
        if i < len(node.items) -1:
            ret_str += val + ","
        else:
            ret_str += val 

    return ret_str + '}'


def eval_dict(node, env):
    return {eval_expression(key, env): eval_expression(value, env) for key, value in node.items}


def eval_return(node, env):
    return "return " + str(eval_expression(node.value, env)) + ";" if node.value is not None else "return ;"


evaluators = {
    ast.Number: lambda node, env: str(node.value),
    ast.String: lambda node, env: 'string("' + str(node.value) + '")',
    ast.Array: eval_array,
    ast.Dictionary: eval_dict,
    ast.Identifier: eval_identifier,
    ast.BinaryOperator: eval_binary_operator,
    ast.UnaryOperator: eval_unary_operator,
    ast.SubscriptOperator: eval_getitem,
    ast.Assignment: eval_assignment,
    ast.Condition: eval_condition,
    ast.Match: eval_match,
    ast.WhileLoop: eval_while_loop,
    ast.ForLoop: eval_for_loop,
    ast.Function: eval_function_declaration,
    ast.Call: eval_call,
    ast.Return: eval_return,
    ast.TypedName: eval_typed_var, 
    ast.UsingNode: eval_include, 
    ast.ClassDefinition: eval_classdef,
    ast.ClassAccess: eval_classaccess, 
    ast.GroupExpression: eval_group, 
    ast.Enum: eval_enum, 
    ast.Cpp: eval_cpp, 
    ast.InferedName: eval_auto_var
}


def eval_node(node, env):
    tp = type(node)
    if tp in evaluators:
        return evaluators[tp](node, env)
    else:
        raise Exception('Unknown node {} {}'.format(tp.__name__, node))


def eval_expression(node, env):
    return eval_node(node, env)


def eval_statement(node, env):
    return eval_node(node, env)


def eval_statements(statements, env):
    ret = None
    str_res = ""
    for statement in statements:
        if isinstance(statement, ast.Break):
            str_res += '\nbreak;'
            continue
        elif isinstance(statement, ast.Continue):
            str_res += '\ncontinue;'
            continue
        else:
            ret = eval_statement(statement, env)
            str_res += "\n" + str(ret) 


    return str_res


def add_builtins(env):
    builtins = {
        "null":"null", 
        "true":"true",
        "false": "false", 
        "COLOR_ERROR": 'color', 
        "COLOR_CLEAR": 'color', 
        "COLOR_SUCCESS": 'color', 
        'print': ast.Function(ast.Identifier('print'), ['message'], [], 'void'),
        'exit': ast.Function(ast.Identifier('exit'), ['code'], [], 'void'),
        'log': ast.Function(ast.Identifier('log'), ['log_message'], [], 'void'),
        'logf': ast.Function(ast.Identifier('logf'), ['file', 'log_message'], [], 'void'),
        'slice': ast.Function(ast.Identifier('slice'), ['str|arr', 'start', 'end'], [], 'void'),
        'println': ast.Function(ast.Identifier('println'), ['message'], [], 'void'),
        'len': ast.Function(ast.Identifier('len'), ['array'], [], 'size'),
        'open': ast.Function(ast.Identifier('open'), ['filename', 'mode'], [], 'file'),
        'readfile': ast.Function(ast.Identifier('readfile'), ['filePtr'], [], 'string'), 
        'closefile': ast.Function(ast.Identifier('closefile'), ['filePtr'], [], 'i32'), 
        'readline': ast.Function(ast.Identifier('readline'), [], [], 'string'),
        'string': ast.Function(ast.Identifier('string'), ['convert'], [], 'string')
    }

    for key in builtins.keys():
        env.set(key, builtins[key])


def create_global_env():
    env = Environment()
    add_builtins(env)
    return env


def evaluate_env(s, env, verbose=False, file=False):
    lexer = Lexer(s.name)
    try:
        tokens = lexer.tokenize(s.read())
    except AbrvalgSyntaxError as err:
        report_syntax_error(lexer, err)
        if verbose:
            raise
        else:
            return

    if verbose:
        print('Tokens')
        print_tokens(tokens)
        print()

    token_stream = TokenStream(tokens)

    try:
        program = Parser().parse(token_stream)
    except AbrvalgSyntaxError as err:
        report_syntax_error(lexer, err)
        if verbose:
            raise
        else:
            return

    if verbose:
        print('AST')
        print_ast(program.body)
        print()

    env.lexer = lexer
    ret = eval_statements(program.body, env)

    if verbose:
        print('Environment')
        print_env(env)
        print()

    return "{}".format(ret)


def evaluate(s, verbose=False):
    return evaluate_env(s, create_global_env(), verbose)
