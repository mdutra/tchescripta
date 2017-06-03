from ply import lex
import sys

reserved = {
    'mais' : 'OP_ADD',
    'menos' : 'OP_SUB',
    'vezes' : 'OP_MUL',
    'dividido' : 'OP_DIV',
    'por' : 'OP_BY',
    'incrementa' : 'OP_INC',
    'decrementa' : 'OP_DEC',
    'na' : 'OP_EXP',
    'se' : 'KW_IF',
    'então' : 'KW_IF_OPEN',
    'senão' : 'KW_ELSE',
    'para' : 'KW_FOR',
    'faça' : 'KW_LOOP_OPEN',
    'enquanto' : 'KW_WHILE',
    'int' : 'KW_INT',
    'real' : 'KW_FLOAT',
    'texto' : 'KW_STRING',
    'lista' : 'KW_LIST',
    'mostra' : 'KW_PRINT',
    'leia' : 'KW_INPUT',
    'verdadeiro' : 'TRUE',
    'falso' : 'FALSE',
    'define' : 'KW_FUNCTION',
    'com' : 'KW_FUNC_OPEN_ARGS',
    'como' : 'KW_FUNC_OPEN',
    'não' : 'KW_NOT',
    'é' : 'KW_IS',
    'igual' : 'KW_EQUAL',
    'a' : 'KW_TO',
    'diferente' : 'KW_DIFF',
    'menor' : 'KW_LESS',
    'que' : 'KW_THAN',
    'ou' : 'KW_OR',
    'maior' : 'KW_GREATER',
    'e' : 'KW_AND',
    'deu' : 'KW_DONE',
    'retorna' : 'KW_RETURN',
    'tá' : 'KW_ITS',
    'bom' : 'KW_OK',
    'bota' : 'KW_PUT',
    'em' : 'KW_IN'
}

tokens = [
    'PAR_OPEN',
    'PAR_CLOSE',
    'BRACKET_OPEN',
    'BRACKET_CLOSE',
    'IDENTIFIER',
    'INT_NUMBER',
    'FLOAT_NUMBER',
    'STRING',
    'KW_FUNC_ARGS_SEP',
    'KW_FPUNC'
] + list(reserved.values())


t_PAR_OPEN = r'\('
t_PAR_CLOSE = r'\)'
t_BRACKET_OPEN = r'\['
t_BRACKET_CLOSE = r'\]'
t_KW_FUNC_ARGS_SEP = r','
t_KW_FPUNC = r'\.'


def t_IDENTIFIER(t):
    r'[a-Я][a-Я0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER');
    return t


def t_STRING(t):
    r'\".*\"|\'.*\''
    # Remove the first and the last character.
    t.value = t.value[1:-1];
    return t


def t_float_error(t):
    r'([0-9]+,[0-9]*,[0-9]+)+'
    print('Token ilegal: {} na linha {}'.format(t.value, t.lineno))
    t.lexer.skip(1)


def t_FLOAT_NUMBER(t):
    r'[0-9]+,[0-9]+'
    t.value = t.value.replace(',', '.')
    t.value = float(t.value) # Convert to float
    return t


def t_INT_NUMBER(t):
    r'[0-9]+'
    t.value = int(t.value) # Convert to integer
    return t


def t_NEW_LINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print('Caractere ilegal: {} na linha {}'.format(t.value[0], t.lineno))
    t.lexer.skip(1)

def t_COMMENT(t):
    r'\#.*'
    pass
    # No return value. Token discarded


t_ignore = ' \t'
#t_ignore_COMMENT = r'\#.*'


lexer = lex.lex()


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print('Uso: {} ARQUIVO'.format(sys.argv[0]))
    else:
        file = open(sys.argv[1], 'r')
        data = file.read();

        lexer.input(data)

        while True:
            token = lexer.token()
            if not token:
                break
            print(token)

        file.close()
