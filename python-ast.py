import ast

ast.num(5)
ast.str(s)
ast.list(elementos, load|store)
ast.name(id, load|store)
ast.expr(valor)
ast.unary(operador, operando)
operador:
    ast.uadd
    ast.usub
    ast.not
ast.binop(esq, op, dir)
op:
    ast.add pow
    ast.sub
    ast.mult
    ast.div

boolop(op,valores)
compare(esq,ops,comparadores)
ops:
    eq noteq lt lte gt gte is isnot in not in
nameconstant(valor)
    true
    false
    none

FLUXO
if(teste,body,orelse)
for(target,iter,body,orelse)
while(teste, body, orelse)
--
call(func, args, keywords, não precisa, não precisa)
assign(targets, valor)
        [name]   nó
functionDef(name, args, body, não precisa, returns?)
arguments(args, não precisa o resto)
arg(arg, anotações)
            tipo
return(valor)
