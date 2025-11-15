# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

# Lexico

class TokenType:
    ID   = "ID"
    INT  = "INT"
    REAL = "REAL"
    PLUS = "PLUS"
    MINUS= "MINUS"
    MUL  = "MUL"
    DIV  = "DIV"
    ASSIGN = "ASSIGN"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF    = "EOF"

@dataclass
class Token:
    type: str
    lexeme: str
    pos: int

class Lexer:
    def __init__(self, s: str):
        self.s = s
        self.i = 0
        self.n = len(s)

    def _skip_ws(self):
        while self.i < self.n and self.s[self.i].isspace():
            self.i += 1

    def next(self) -> Token:
        self._skip_ws()
        if self.i >= self.n:
            return Token(TokenType.EOF, "", self.i)

        c = self.s[self.i]

        # Identificadores (variables) estilo Python simple: [a-zA-Z_][a-zA-Z0-9_]*
        if c.isalpha() or c == '_':
            j = self.i
            self.i += 1
            while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] == '_'):
                self.i += 1
            return Token(TokenType.ID, self.s[j:self.i], j)

        # Numeros: INT o REAL
        if c.isdigit() or c == '.':
            j = self.i
            dot = (c == '.')
            self.i += 1
            while self.i < self.n:
                t = self.s[self.i]
                if t.isdigit():
                    self.i += 1
                elif t == '.' and not dot:
                    dot = True
                    self.i += 1
                else:
                    break
            lex = self.s[j:self.i]
            if lex.count('.') == 0:
                return Token(TokenType.INT, lex, j)
            else:
                if lex.startswith('.'):
                    lex = '0' + lex
                if lex.endswith('.'):
                    lex = lex + '0'
                return Token(TokenType.REAL, lex, j)

        # Simbolos
        self.i += 1
        if c == '+': return Token(TokenType.PLUS, "+", self.i-1)
        if c == '-': return Token(TokenType.MINUS, "-", self.i-1)
        if c == '*': return Token(TokenType.MUL, "*", self.i-1)
        if c == '/': return Token(TokenType.DIV, "/", self.i-1)
        if c == '=': return Token(TokenType.ASSIGN, "=", self.i-1)
        if c == '(': return Token(TokenType.LPAREN, "(", self.i-1)
        if c == ')': return Token(TokenType.RPAREN, ")", self.i-1)

        raise SyntaxError(f"Simbolo lexico desconocido en posicion {self.i-1}: '{c}'")

# AST

class AST:
    def __init__(self):
        self.val: Optional[float] = None
        self.ty: Optional[str] = None
    def accept(self, v): raise NotImplementedError

class Num(AST):
    def __init__(self, lex: str, is_real: bool):
        super().__init__()
        self.lex = lex
        self.is_real = is_real
        self.ty = 'real' if is_real else 'int'
        self.val = float(lex) if is_real else int(lex)
    def accept(self, v): return v.visit_Num(self)

class Var(AST):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def accept(self, v): return v.visit_Var(self)

class Assign(AST):
    def __init__(self, name: str, expr: AST):
        super().__init__()
        self.name = name
        self.expr = expr
    def accept(self, v): return v.visit_Assign(self)

class Op:
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"

class Binary(AST):
    def __init__(self, op: str, left: AST, right: AST):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right
    def accept(self, v): return v.visit_Binary(self)

# Tabla de simbolos

@dataclass
class SymEntry:
    name: str
    ty: str  # 'int' | 'real'

class SymTable:
    def __init__(self):
        self.map: Dict[str, SymEntry] = {}
    def lookup(self, name: str) -> Optional[SymEntry]:
        return self.map.get(name)
    def insert(self, name: str, ty: str) -> SymEntry:
        e = SymEntry(name, ty)
        self.map[name] = e
        return e
    def set_type(self, name: str, ty: str):
        e = self.lookup(name)
        if e is None:
            self.insert(name, ty)
        else:
            # Si se mezclan tipos (int/real), promovemos a real
            if e.ty != ty:
                e.ty = 'real'
    def __str__(self) -> str:
        return "{" + ", ".join(f"{k}:{v.ty}" for k, v in self.map.items()) + "}"

# Parser LL(1) + EDTS

class Parser:
    def __init__(self, lx: Lexer):
        self.toks: List[Token] = []
        t = lx.next()
        self.toks.append(t)
        while t.type != TokenType.EOF:
            t = lx.next()
            self.toks.append(t)
        self.k = 0

    def LA(self) -> Token:
        return self.toks[self.k]

    def match(self, tt: str) -> Token:
        t = self.LA()
        if t.type != tt:
            raise SyntaxError(f"Se esperaba {tt} y se encontro {t.type} (pos {t.pos})")
        self.k += 1
        return t

    def parseStmt(self) -> AST:
        """
        Stmt → id '=' Exp
             | Exp
        """
        if self.LA().type == TokenType.ID and (self.k+1) < len(self.toks) and self.toks[self.k+1].type == TokenType.ASSIGN:
            idtok = self.match(TokenType.ID)
            self.match(TokenType.ASSIGN)
            e = self.parseExp()
            return Assign(idtok.lexeme, e)
        return self.parseExp()

    def parseExp(self) -> AST:
        """
        Exp → Exp '+' Term
            | Exp '-' Term
            | Term
        (implementado como Exp → Term Exp')
        """
        t = self.parseTerm()
        return self.parseExpPrime(t)

    def parseExpPrime(self, inherited: AST) -> AST:
        if self.LA().type == TokenType.PLUS:
            self.match(TokenType.PLUS)
            t = self.parseTerm()
            return self.parseExpPrime(Binary(Op.ADD, inherited, t))
        if self.LA().type == TokenType.MINUS:
            self.match(TokenType.MINUS)
            t = self.parseTerm()
            return self.parseExpPrime(Binary(Op.SUB, inherited, t))
        return inherited  # ε

    def parseTerm(self) -> AST:
        """
        Term → Term '*' Factor
             | Term '/' Factor
             | Factor
        (implementado como Term → Factor Term')
        """
        f = self.parseFactor()
        return self.parseTermPrime(f)

    def parseTermPrime(self, inherited: AST) -> AST:
        if self.LA().type == TokenType.MUL:
            self.match(TokenType.MUL)
            f = self.parseFactor()
            return self.parseTermPrime(Binary(Op.MUL, inherited, f))
        if self.LA().type == TokenType.DIV:
            self.match(TokenType.DIV)
            f = self.parseFactor()
            return self.parseTermPrime(Binary(Op.DIV, inherited, f))
        return inherited  # ε

    def parseFactor(self) -> AST:
        """
        Factor → '(' Exp ')'
               | id
               | num
               | '+' Factor
               | '-' Factor
        """
        tt = self.LA().type
        if tt == TokenType.PLUS:
            self.match(TokenType.PLUS)
            return self.parseFactor()  # +F ≡ F
        if tt == TokenType.MINUS:
            self.match(TokenType.MINUS)
            # -F ≡ 0 - F
            return Binary(Op.SUB, Num("0", is_real=False), self.parseFactor())
        if tt == TokenType.LPAREN:
            self.match(TokenType.LPAREN)
            e = self.parseExp()
            self.match(TokenType.RPAREN)
            return e
        if tt == TokenType.INT:
            t = self.match(TokenType.INT)
            return Num(t.lexeme, is_real=False)
        if tt == TokenType.REAL:
            t = self.match(TokenType.REAL)
            return Num(t.lexeme, is_real=True)
        if tt == TokenType.ID:
            name = self.match(TokenType.ID).lexeme
            return Var(name)
        raise SyntaxError(f"Se esperaba Factor y se encontro {tt} (pos {self.LA().pos})")


class TypeAndEval:
    def __init__(self, st: SymTable):
        self.st = st

    def visit_Num(self, n: Num):
        # ya tiene .ty y .val
        return n.val

    def visit_Var(self, v: Var):
        sym = self.st.lookup(v.name)
        if sym is None:
            raise NameError(f"Variable no definida: {v.name}")
        v.ty = sym.ty
        return None

    def visit_Assign(self, a: Assign):
        val = a.expr.accept(self)
        expr_ty = a.expr.ty
        if expr_ty is None:
            raise TypeError(f"No se puede asignar valor sin tipo a '{a.name}'")
        self.st.set_type(a.name, expr_ty)
        a.ty = expr_ty
        return val

    def visit_Binary(self, b: Binary):
        lv = b.left.accept(self)
        rv = b.right.accept(self)
        lt = b.left.ty
        rt = b.right.ty
        if lt == 'real' or rt == 'real':
            b.ty = 'real'
        elif lt == 'int' and rt == 'int':
            b.ty = 'int'
        else:
            b.ty = 'real'
        # evaluación solo si ambos son Num
        if isinstance(b.left, Num) and isinstance(b.right, Num):
            if b.op == Op.ADD: b.val = b.left.val + b.right.val
            elif b.op == Op.SUB: b.val = b.left.val - b.right.val
            elif b.op == Op.MUL: b.val = b.left.val * b.right.val
            elif b.op == Op.DIV: b.val = b.left.val / b.right.val
        return b.val

# TAC

@dataclass
class Quad:
    op: str
    a1: Optional[str]
    a2: Optional[str]
    res: str

class TempFactory:
    def __init__(self):
        self.c = 0
    def new(self) -> str:
        self.c += 1
        return f"t{self.c}"

class TACGen:
    def __init__(self, st: SymTable):
        self.st = st
        self.tf = TempFactory()
        self.code: List[Quad] = []

    def emit(self, op: str, a1: Optional[str], a2: Optional[str], res: str):
        self.code.append(Quad(op, a1, a2, res))
        return res

    def load_const(self, n: Num) -> Tuple[str, str]:
        t = self.tf.new()
        if n.ty == 'int':
            self.emit("LDCI", n.lex, None, t)
        else:
            self.emit("LDCR", n.lex, None, t)
        return t, n.ty

    def load_var(self, v: Var) -> Tuple[str, str]:
        sym = self.st.lookup(v.name)
        if sym is None:
            raise NameError(f"Variable '{v.name}' no definida")
        # usamos el nombre directo como "registro"/posición
        return v.name, sym.ty

    def coerce(self, place: str, ty_src: str, ty_dst: str) -> Tuple[str, str]:
        if ty_src == ty_dst:
            return place, ty_dst
        if ty_src == 'int' and ty_dst == 'real':
            t = self.tf.new()
            self.emit("ITOR", place, None, t)
            return t, 'real'
        # no hacemos real -> int implícito
        return place, ty_src

    def gen(self, n: AST) -> Tuple[str, str]:
        if isinstance(n, Num):
            return self.load_const(n)
        if isinstance(n, Var):
            return self.load_var(n)
        if isinstance(n, Assign):
            place, ty = self.gen(n.expr)
            self.st.set_type(n.name, ty)
            self.emit("STORR" if ty=='real' else "STORI", place, None, n.name)
            return n.name, ty
        if isinstance(n, Binary):
            lplace, lty = self.gen(n.left)
            rplace, rty = self.gen(n.right)
            ty_res = 'real' if (lty=='real' or rty=='real') else 'int'
            lplace, _ = self.coerce(lplace, lty, ty_res)
            rplace, _ = self.coerce(rplace, rty, ty_res)
            t = self.tf.new()
            suf = 'R' if ty_res=='real' else 'I'
            if n.op == Op.ADD: op = f"ADD{suf}"
            elif n.op == Op.SUB: op = f"SUB{suf}"
            elif n.op == Op.MUL: op = f"MUL{suf}"
            else: op = f"DIV{suf}"
            self.emit(op, lplace, rplace, t)
            return t, ty_res
        raise RuntimeError("Nodo AST no soportado en TAC")

    def dump(self) -> str:
        lines = []
        for q in self.code:
            if q.a2 is None and q.a1 is not None:
                lines.append(f"{q.op} {q.a1} -> {q.res}")
            elif q.a1 is not None and q.a2 is not None:
                lines.append(f"{q.op} {q.a1}, {q.a2} -> {q.res}")
            else:
                lines.append(f"{q.op} -> {q.res}")
        return "\n".join(lines)

# Arbol ASCII del AST

class AsciiTreePrinter:
    def _label(self, n: AST) -> str:
        if isinstance(n, Num): return f"Num({n.lex})"
        if isinstance(n, Var): return f"Var({n.name})"
        if isinstance(n, Assign): return f"Assign({n.name})"
        if isinstance(n, Binary):
            m = {Op.ADD:"+", Op.SUB:"-", Op.MUL:"*", Op.DIV:"/"}[n.op]
            return f"Binary({m})"
        return n.__class__.__name__
    def _kids(self, n: AST):
        if isinstance(n, Assign): return [n.expr]
        if isinstance(n, Binary): return [n.left, n.right]
        return []
    def print(self, node: AST) -> str:
        out: List[str] = []
        def walk(n: AST, pre: str = "", last: bool = True):
            out.append(pre + ("└── " if last else "├── ") + self._label(n))
            kids = self._kids(n)
            if not kids: return
            new_pre = pre + ("    " if last else "│   ")
            for i, ch in enumerate(kids):
                walk(ch, new_pre, i == len(kids)-1)
        walk(node, "", True)
        return "\n".join(out)

# Main

def main():
    print("EDTS estilo Python: escribe una expresion. Enter vacío o 'exit' para salir.")
    st = SymTable()
    while True:
        try:
            line = input(">>> ").strip()
        except EOFError:
            break
        if not line or line.lower() == "exit":
            break
        try:
            parser = Parser(Lexer(line))
            ast = parser.parseStmt()

            typer = TypeAndEval(st)
            try:
                ast.accept(typer)
            except NameError:
                pass

            # Generar TAC
            tac = TACGen(st)
            tac.gen(ast)

            # Salidas
            print("Arbol ASCII del AST:")
            print(AsciiTreePrinter().print(ast))
            print("Tabla de símbolos:", st)
            print("Codigo en Tres Direcciones (TAC):")
            print(tac.dump())
        except Exception as ex:
            print("Error:", ex)
    print("Fin.")

if __name__ == "__main__":
    main()
