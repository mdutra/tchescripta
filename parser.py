import sys
from ply import yacc
from scanner import tokens
import ast

scope = []
t = ""

class Node:
    def __init__(self, type, children=None, leaf=None, datatype=None):
        self.type = type
        if children:
            if not isinstance(children, (list, tuple)):
                children = [children]
            self.children = children
        else:
            self.children = []
        self.leaf = leaf
        self.datatype = datatype


    def _pretty(self, prefix='| '):
        string = []
        root = '{}'.format(str(self.type))
        if self.leaf is not None:
            root += ' ({})'.format(self.leaf)
        if self.datatype is not None:
            root += ' [{}]'.format(self.datatype)
        string.append(root)
        for child in self.children:
            if isinstance(child, Node):
                for child_string in child._pretty():
                    string.append('{}{}'.format(prefix, child_string))
            else:
                string.append('{}{}'.format(prefix, child))
        return string


    def pretty(self):
        return '\n'.join(self._pretty())


    def __str__(self):
        children_string = ', '.join([str(c) for c in self.children]) if self.children else ''
        leaf_string = '{} '.format(self.leaf) if self.leaf is not None else ''
        return '({} {}[{}])'.format(self.type, leaf_string, children_string)


    def visit(self):
        if self.type == 'funcao':
            #start new scope
            scope.append(None)
            self.children[0].visit()
            if len(self.children) > 1:
                self.children[1].visit()
            while scope.pop(): pass

        elif self.type == 'corpo' or self.type == 'para' or self.type == 'enquanto':
            scope.append(None)
            for child in self.children:
                if isinstance(child, Node):
                    child.visit()
            while scope.pop(): pass
        elif self.type == 'definicao_loop':
            # caso "para A em B faça"
            # Verifica se B está no escopo
            for var in scope[::-1]:
                if var and var[0] == self.children[1]:
                    break
            else:
                print("{} não foi definido".format(self.children[1]))

            # Adiciona A no escopo (falta o tipo)
            scope.append((self.children[0], None))

        elif self.type == 'var':
            scope.append((self.children[0], self.leaf))

        elif self.type == 'declaracao':
            global t
            t = self.leaf
            self.children[0].visit()

        elif self.type == 'atribuicao':
            if (len(self.children) > 1):
                self.children[1].visit()
                if self.children[1].datatype and t != self.children[1].datatype:
                    print("Atribuição com conflito de tipos: {} - {}".format(t, self.children[1].datatype))

            scope.append((self.children[0], t))

        elif self.type == 'acao_atribuicao':
            for var in scope[::-1]:
                if var and var[0] == self.children[0]:
                    if self.children[1].datatype and var[1] != self.children[1].datatype:
                        print("Atribuição com conflito de tipos: {} - {}".format(var[1], self.children[1].datatype))
                    break
            else:
                print("{} não foi definido".format(self.children[0]))
            self.children[1].visit()

        elif self.type == 'id':
            for var in scope[::-1]:
                if var and var[0] == self.leaf:
                    break
            else:
                print("{} não foi definido".format(self.leaf))

        elif self.type == 'bin_op' or self.type == 'comp_op':
            for child in self.children:
                val_type = ''
                if isinstance(child, Node):
                    child.visit()
                if child.type == 'id':
                    for var in scope[::-1]:
                        if var and var[0] == child.leaf:
                            val_type = var[1]
                            break
                else:
                    val_type = child.datatype

                if val_type == 'int':
                    if self.type == 'comp_op':
                        self.datatype = 'bool'
                    elif self.datatype != 'real':
                        self.datatype = 'int'
                    # Todas as operações de dividir retornam "real"
                    if self.leaf == 'dividido_por':
                        self.datatype = 'real'
                elif val_type == 'real':
                    if self.type == 'comp_op':
                        self.datatype = 'bool'
                    else:
                        self.datatype = 'real'
                elif val_type:
                    print('A operação {} não suporta o tipo {}.'.format(self.leaf, val_type))

        elif self.type == 'log_op':
            for child in self.children:
                val_type = ''
                if isinstance(child, Node):
                    child.visit()
                if child.type == 'id':
                    for var in scope[::-1]:
                        if var and var[0] == child.leaf:
                            val_type = var[1]
                            break
                else:
                    val_type = child.datatype

                if val_type == 'bool':
                    self.datatype = 'bool'
                elif val_type:
                    print('A operação {} não suporta o tipo {}.'.format(self.leaf, val_type))

        elif self.type == 'unary_op':
            val_type = ''
            if self.children[0].type == 'id':
                for var in scope[::-1]:
                    if var and var[0] == self.children[0].leaf:
                        val_type = var[1]
                        break
            else:
                val_type = child.datatype

            if val_type == 'int':
                self.datatype = 'int'
            elif val_type:
                print('A operação {} não suporta o tipo {}.'.format(self.leaf, val_type))

        elif self.type == 'teste':
            for child in self.children:
                if isinstance(child, Node):
                    child.visit()
            if self.children[0].datatype and self.children[0].datatype != 'bool':
                print('Condição não aceita o tipo {}.'.format(self.children[0].datatype))

        else:
            for child in self.children:
                if isinstance(child, Node):
                    child.visit()


    def to_python_ast(self):
        op = {
                'mais': ast.Add,
                'menos': ast.Sub,
                'vezes': ast.Mult,
                'dividido_por': ast.Div,
                'na': ast.Pow,
                'e': ast.And,
                'ou': ast.Or,
                'não': ast.Not,
                'verdadeiro': True,
                'falso': False,
                'é_igual_a': ast.Eq,
                'é_diferente_de': ast.NotEq,
                'é_menor_que': ast.Lt,
                'é_menor_ou_igual_a': ast.LtE,
                'é_maior_que': ast.Gt,
                'é_maior_ou_igual_a': ast.GtE,
                'incrementa': ast.Add,
                'decrementa': ast.Sub
        }


        if self.type == 'comando':
            c1 = self.children[0].to_python_ast()
            if len(self.children) > 1:
                c2 = self.children[1].to_python_ast()
                if isinstance(c2, list):
                    c1.extend(c2)
                else:
                    c1.append(c2)
                return c1
            else:
                if isinstance(c1, list):
                    return c1
                else:
                    return [c1]
        elif self.type == 'bin_op':
            return ast.BinOp(self.children[0].to_python_ast(), op[self.leaf](), self.children[1].to_python_ast())
        elif self.type == 'log_op':
            if self.leaf == 'não':
                return ast.UnaryOp(op[self.leaf](), self.children[0].to_python_ast())
            else:
                return ast.BoolOp(op[self.leaf](), [self.children[0].to_python_ast(), self.children[1].to_python_ast()])
        elif self.type == 'comp_op':
            return ast.Compare(self.children[0].to_python_ast(), [op[self.leaf]()], [self.children[1].to_python_ast()])
        elif self.type == 'paren':
            return self.children[0].to_python_ast()
        elif self.type == 'valor_int' or self.type == 'valor_real':
            return ast.Num(self.leaf)
        elif self.type == 'valor_texto':
            return ast.Str(self.leaf)
        elif self.type == 'valor_bool':
            return ast.NameConstant(op[self.leaf])
        elif self.type == 'id':
            return ast.Name(self.leaf, ast.Load())
        elif self.type == 'acao_atribuicao':
            if len(self.children) > 2:
                target = ast.Name(self.children[0], ast.Load())
                ind = self.children[1].to_python_ast()
                value = self.children[2].to_python_ast()
                target = ast.Subscript(target, ind, ast.Store())
            else:
                target = ast.Name(self.children[0], ast.Store())
                value = self.children[1].to_python_ast()
            return ast.Assign([target], value)
        elif self.type == 'indice':
            return ast.Index(self.children[0].to_python_ast())
        elif self.type == 'vetor':
            target = ast.Name(self.children[0], ast.Load())
            ind = self.children[1].to_python_ast()
            return ast.Subscript(target, ind, ast.Load())
        elif self.type == 'declaracao':
            return self.children[0].to_python_ast()
        elif self.type == 'atribuicao':
            target = ast.Name(self.children[0], ast.Store())
            if len(self.children) > 1:
                if self.children[1].type == 'range':
                    value = ast.List(self.children[1].to_python_ast(), ast.Load())
                else:
                    value = self.children[1].to_python_ast()
                return ast.Assign([target], value)
            else:
                return target
        elif self.type == 'range':
            val1 = self.children[0].to_python_ast()
            val2 = self.children[1].to_python_ast()
            if isinstance(val1, ast.Num) and isinstance(val2, ast.Num):
                el = []
                for v in range(val1.n, val2.n):
                    el.append(ast.Num(v))
                return el
            return None
        elif self.type == 'func':
            args_nodes = self.children[1].to_python_ast()
            if not isinstance(args_nodes, list):
                args_nodes = [args_nodes]

            if self.children[0] == 'mostra':
                func_node = ast.Name(id='print', ctx=ast.Load())
            elif self.children[0] == 'leia':
                func_node = ast.Name(id='input', ctx=ast.Load())

            return ast.Expr(ast.Call(func_node, args_nodes, []))
        elif self.type == 'lista_args' or self.type == 'lista_atribuicoes' or self.type == 'lista_params':
            n1 = self.children[0].to_python_ast()
            n2 = self.children[1].to_python_ast()
            if isinstance(n1, list):
                n1.append(n2)
                return n1
            else:
                return [n1, n2]
        elif self.type == 'condicao':
            teste = self.children[0].to_python_ast()
            corpo = self.children[1].to_python_ast()
            if self.children[2] == 'e_deu':
                senaose = []
            else:
                senaose = self.children[2].to_python_ast()

            return ast.If(teste, corpo, senaose)
        elif self.type == 'teste' or self.type == 'corpo' or self.type == 'senão' or self.type == 'corpo_loop':
            return self.children[0].to_python_ast()
        elif self.type == 'senão se':
            return [self.children[0].to_python_ast()]
        elif self.type == 'enquanto':
            return ast.While(self.children[0].to_python_ast(), self.children[1].to_python_ast(), [])
        elif self.type == 'var':
            return ast.arg(self.children[0], None)
        elif self.type == 'inside_funcion':
            return self.children[0].to_python_ast()
        elif self.type == 'funcao':
            if len(self.children) > 1:
                params = ast.arguments(self.children[0].to_python_ast(), None, [], [], None, [])
                corpo = self.children[1].to_python_ast()
            else:
                params = ast.arguments([], None, [], [], None, [])
                corpo = self.children[0].to_python_ast()
            return ast.FunctionDef(self.leaf, params, corpo, [], None)
        elif self.type == 'retorna':
            return ast.Return(self.children[0].to_python_ast())
        elif self.type == 'func_com':
            args = self.children[0].to_python_ast()
            return ast.Expr(ast.Call(ast.Name(self.leaf, ast.Load()), args, []))
        elif self.type == 'unary_op':
            target = ast.Name(self.children[0].leaf, ast.Store())
            return ast.AugAssign(target, op[self.leaf](), ast.Num(1))
        elif self.type == 'para':
            definicao = self.children[0].to_python_ast()
            corpo_loop = self.children[1].to_python_ast()
            return ast.For(definicao[0], definicao[1], corpo_loop, [])
        elif self.type == 'definicao_loop':
            return [
                ast.Name(self.children[0], ast.Store()),
                ast.Name(self.children[1], ast.Load()),
            ]




precedence = (
        # ('left', 'KW_IS', 'KW_TO', 'KW_DIFF'),
        ('right', 'KW_FUNC_OPEN_ARGS', 'KW_PRINT', 'KW_INPUT', 'IDENTIFIER', 'KW_FUNC_ARGS_SEP'),
        ('left', 'KW_OR', 'KW_AND', 'KW_NOT'),
        ('left', 'COMP', 'KW_IS'),
        ('left', 'OP_ADD', 'OP_SUB'),
        ('left', 'OP_MUL', 'OP_DIV', 'OP_BY'),
        ('left', 'OP_INC', 'OP_DEC'),
        ('left', 'OP_EXP'),
        #('left', 'KW_PUT')
)


def p_codigo(p):
    '''codigo : codigo comando KW_FPUNC
              | comando KW_FPUNC
    '''
    if p.slice[1].type == "codigo":
        p[0] = Node('comando', children=[p[1], p[2]])
    else:
        p[0] = Node('comando', children=[p[1]])


def p_comando(p):
    '''comando : declaracao
               | acao
    '''
    p[0] = p[1]


def p_declaracao(p):
    '''declaracao : tipo lista_atribuicoes
    '''
    p[0] = Node('declaracao', children=[p[2]], leaf=p[1])


def p_declaracao_funcao(p):
    '''declaracao : funcao_inicio funcao_fim
                  | funcao_inicio KW_FUNC_OPEN_ARGS lista_params funcao_fim
    '''
    if p.slice[2].type == "funcao_fim":
        p[0] = Node('funcao', children=[p[2]], leaf=p[1])
    else:
        p[0] = Node('funcao', children=[p[3], p[4]], leaf=p[1])


def p_declaracao_funcao_inicio(p):
    '''funcao_inicio : KW_FUNCTION IDENTIFIER
    '''
    p[0] = p[2]


def p_declaracao_funcao_fim(p):
    '''funcao_fim : KW_FUNC_OPEN codigo KW_AND KW_DONE
    '''
    p[0] = Node('inside_funcion', children=[p[2]])


def p_lista_params(p):
    '''lista_params : lista_params KW_FUNC_ARGS_SEP param
                    | param
    '''
    if p.slice[1].type == "lista_params":
        p[0] = Node('lista_params', children=[p[1], p[3]])
    else:
        p[0] = p[1]


def p_param(p):
    'param : tipo IDENTIFIER'
    p[0] = Node('var', children=[p[2]], leaf=p[1])


def p_tipo(p):
    '''tipo : KW_INT
            | KW_FLOAT
            | KW_STRING
            | KW_LIST
    '''
    p[0] = p[1]


def p_lista_atribuicoes(p):
    '''lista_atribuicoes : lista_atribuicoes KW_FUNC_ARGS_SEP atribuicao
                         | atribuicao
    '''
    if p.slice[1].type == "lista_atribuicoes":
        p[0] = Node('lista_atribuicoes', children=[p[1], p[3]])
    else:
        p[0] = p[1]


def p_atribuicao(p):
    'atribuicao : IDENTIFIER'
    p[0] = Node('atribuicao', children=[p[1]])


def p_atribuicao_valor(p):
    'atribuicao : IDENTIFIER KW_IS expressao'
    p[0] = Node('atribuicao', children=[p[1], p[3]], leaf=p[2])


def p_atribuicao_lista(p):
    'atribuicao : IDENTIFIER KW_IS expressao KW_TO expressao'
    range = Node('range', children=[p[3], p[5]])
    p[0] = Node('atribuicao', children=[p[1], range], leaf=p[2])


def p_acao_expressao(p):
    '''acao : expressao
            | condicao
    '''
    p[0] = p[1]


def p_acao_retorna(p):
    'acao : KW_RETURN expressao'
    p[0] = Node('retorna', children=[p[2]], leaf=p[1])


def p_acao_atribuicao(p):
    'acao : IDENTIFIER KW_IS expressao'
    p[0] = Node('acao_atribuicao', children=[p[1], p[3]], leaf=p[2])


#Tem um shift/reduce entre esses e "expressao -> idf[e]"
def p_acao_atribuicao_vetor(p):
    'acao : IDENTIFIER BRACKET_OPEN expressao BRACKET_CLOSE KW_IS expressao'
    indice = Node('indice', children=[p[3]])
    p[0] = Node('acao_atribuicao', children=[p[1], indice, p[6]], leaf=p[5])


def p_acao_enquanto(p):
    '''acao : KW_WHILE expressao fim_loop'''
    n1 = Node('teste', children=[p[2]])
    p[0] = Node('enquanto', children=[n1, p[3]])


def p_acao_bota(p):
    'acao : KW_PUT expressao KW_IN IDENTIFIER'
    p[0] = Node('bota', children=[p[2]], leaf=p[4])


def p_acao_para(p):
    '''acao : KW_FOR IDENTIFIER KW_IN IDENTIFIER fim_loop'''
    definicao = Node('definicao_loop', children=[p[2], p[4]], leaf=p[3])
    p[0] = Node('para', children=[definicao, p[5]])


def p_fim_loop(p):
    '''fim_loop :  KW_LOOP_OPEN codigo KW_AND KW_DONE'''
    p[0] = Node('corpo_loop', children=[p[2]])


def p_condicao(p):
    'condicao : KW_IF expressao KW_IF_OPEN codigo fim_condicao'
    n1 = Node('teste', children=[p[2]])
    n2 = Node('corpo', children=[p[4]])
    p[0] = Node('condicao', children=[n1, n2, p[5]])

def p_fim_condicao(p):
    '''fim_condicao : KW_ELSE condicao
                    | KW_ITS KW_OK KW_IF_OPEN codigo fim_condicao
                    | KW_AND KW_DONE
    '''
    if p.slice[1].type == "KW_ELSE":
        p[0] = Node('senão se', children=[p[2]])
    elif p.slice[1].type == "KW_ITS":
        p[0] = Node('senão', children=[p[4], p[5]])
    else:
        p[0] = p[1]+'_'+p[2]


def p_expressao_paren(p):
    'expressao : PAR_OPEN expressao PAR_CLOSE'
    p[0] = Node('paren', children=[p[2]])


def p_expressao_bin(p):
    '''expressao : expressao OP_ADD expressao
                 | expressao OP_SUB expressao
                 | expressao OP_MUL expressao
                 | expressao OP_DIV OP_BY expressao
                 | expressao OP_EXP expressao
                 | expressao KW_AND expressao
                 | expressao KW_OR expressao
                 | expressao comp expressao %prec COMP
    '''
    if p.slice[2].type == "OP_DIV":
        p[0] = Node('bin_op', children=[p[1], p[4]], leaf=p[2]+'_'+p[3])
    elif p.slice[2].type == "comp":
        p[0] = Node('comp_op', children=[p[1], p[3]], leaf=p[2])
    elif p.slice[2].type == "KW_AND" or p.slice[2].type == "KW_OR":
        p[0] = Node('log_op', children=[p[1], p[3]], leaf=p[2])
    else:
        p[0] = Node('bin_op', children=[p[1], p[3]], leaf=p[2])


def p_expressao_unararia(p):
    '''expressao : KW_NOT expressao
                 | OP_INC expressao
                 | OP_DEC expressao
    '''
    if p.slice[1].type == "KW_NOT":
        p[0] = Node('log_op', children=[p[2]], leaf=p[1])
    else:
        p[0] = Node('unary_op', children=[p[2]], leaf=p[1])


def p_expressao_valor(p):
    '''expressao : INT_NUMBER
                 | FLOAT_NUMBER
                 | STRING
                 | TRUE
                 | FALSE
                 | IDENTIFIER
    '''
    val_type = p.slice[1].type
    if val_type == "IDENTIFIER":
        p[0] = Node('id', leaf=p[1])
    elif val_type == "INT_NUMBER":
        p[0] = Node('valor_int', leaf=p[1], datatype="int")
    elif val_type == "FLOAT_NUMBER":
        p[0] = Node('valor_real', leaf=p[1], datatype="real")
    elif val_type == "STRING":
        p[0] = Node('valor_texto', leaf=p[1], datatype="texto")
    else:
        p[0] = Node('valor_bool', leaf=p[1], datatype="bool")


def p_expressao_vetor(p):
    'expressao : IDENTIFIER BRACKET_OPEN expressao BRACKET_CLOSE'
    indice = Node('indice', children=[p[3]])
    p[0] = Node('vetor', children=[p[1], indice])


def p_expressao_chamada(p):
    '''expressao : func lista_args
                 | IDENTIFIER KW_FUNC_OPEN_ARGS lista_args
    '''
    if p.slice[1].type == "func":
        p[0] = Node('func', children=[p[1], p[2]])
    else:
        p[0] = Node('func_com', children=[p[3]], leaf=p[1])


def p_func(p):
    '''func : KW_PRINT
            | KW_INPUT
    '''
    p[0] = p[1]


def p_lista_args(p):
    '''lista_args : lista_args KW_FUNC_ARGS_SEP expressao
                  | expressao
    '''
    if p.slice[1].type == "lista_args":
        p[0] = Node('lista_args', children=[p[1], p[3]], leaf=p[2])
    else:
        p[0] = p[1]


def p_expressao_comp(p):
    'comp : KW_IS comp2'
    p[0] = p[1]+'_'+p[2]


def p_expressao_comp2(p):
    'comp2 : comp3 comp4'
    p[0] = p[1]+'_'+p[2]


def p_expressao_comp22(p):
    '''comp2 : comp5
             | KW_DIFF
    '''
    p[0] = p[1]


def p_expressao_comp3(p):
    '''comp3 : KW_GREATER
             | KW_LESS'''
    p[0] = p[1]


def p_expressao_comp4(p):
    'comp4 : KW_THAN'
    p[0] = p[1]


def p_expressao_comp44(p):
    'comp4 : KW_OR comp5'
    p[0] = p[1]+'_'+p[2]


def p_expressao_comp5(p):
    'comp5 : KW_EQUAL KW_TO'
    p[0] = p[1]+'_'+p[2]


# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


parser = yacc.yacc()

if (len(sys.argv) < 2):
    while True:
        try:
            s = input('calc> ')
        except EOFError:
            break
        if not s:
            continue
        ast = parser.parse(s)
        ast.visit()
        #print(ast.pretty())
else:
    file = open(sys.argv[1], 'r')
    data = file.read();
    myast = parser.parse(data)
    myast.visit()
    #print(myast.pretty())
    tree = myast.to_python_ast()
    tree = ast.Module(tree)
    ast.fix_missing_locations(tree)
    #print(ast.dump(tree))
    exec(compile(tree, filename="<ast>", mode="exec"))

    file.close()
