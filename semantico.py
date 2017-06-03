    def visit_node(node):
        if node.type == 'fun_decl':
            scope.append(None) #start new scope
            visit(node.children[0]) #param_list
            visit(node.children[1]) #body
            while scope.pop(): pass
        elif node.type == 'param_list':
            for c in node.children:
                visit(c)
        elif node.type == 'param':
            scope.append((node.children[0], node.leaf))

########
        for child in node.children:
            visit_node(child)
########
        for var in scope[::-1]:
            if var and var[0]==x:
#type check
                break;
        if not found:
            #erro
