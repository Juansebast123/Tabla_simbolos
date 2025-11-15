# 🐍 Mini-Compilador Python — EDTS + AST + Tabla de Símbolos + TAC

Este proyecto implementa un **mini-compilador** basado en un **subconjunto de Python**, capaz de:

- Construir el **Árbol de Sintaxis Abstracta (AST)** mediante un **Esquema de Traducción Dirigido por la Sintaxis (EDTS)**.
- Generar y mantener una **tabla de símbolos** tipada (`int` / `real`).
- Crear **código intermedio en tres direcciones (TAC)**.
- Mostrar el **AST en formato ASCII**.
- Evaluar parcialmente expresiones constantes.

---

## 📌 1. Gramática utilizada (subconjunto de Python)

Esta es la gramática seleccionada para el proyecto:

```
Stmt     → id '=' Exp
         | Exp

Exp      → Exp '+' Term
         | Exp '-' Term
         | Term

Term     → Term '*' Factor
         | Term '/' Factor
         | Factor

Factor   → '(' Exp ')'
         | id
         | num
         | '+' Factor
         | '-' Factor
```

Características:

- Sintaxis inspirada en Python.
- Soporte para operaciones aritméticas estándar.
- Soporte para expresiones entre paréntesis.
- Unarios `+` y `-`.
- Asignaciones como en Python (`x = ...`).
- Gramática LL(1) adecuada para EDTS.

---

## 📌 2. Atributos y EDTS (Esquema de Traducción Dirigido por la Sintaxis)

### ✔ Atributos utilizados

| No terminal / nodo AST            | Atributos | Descripción |
|----------------------------------|-----------|-------------|
| `Stmt`                           | `.ast`    | Árbol que representa la sentencia completa. |
| `Exp`, `Term`, `Factor`          | `.ast`    | Subárbol correspondiente a la expresión. |
| `Binary`, `Assign`, `Num`, `Var` | `.ty`, `.val` | Tipo (`int`/`real`) y valor (si corresponde). |

---

### ✔ Reglas con EDTS

#### Asignaciones
```
Stmt → id '=' Exp
        { Stmt.ast = Assign(id.lexeme, Exp.ast) }

Stmt → Exp
        { Stmt.ast = Exp.ast }
```

#### Expresiones
```
Exp → Term Exp'
       { Exp.ast = Exp'.apply(Term.ast) }

Exp' → '+' Term Exp'
         { Exp'.apply(x) = Exp'1.apply(Binary(ADD, x, Term.ast)) }

Exp' → '-' Term Exp'
         { Exp'.apply(x) = Exp'1.apply(Binary(SUB, x, Term.ast)) }

Exp' → ε
         { Exp'.apply(x) = x }
```

#### Productos
```
Term → Factor Term'
         { Term.ast = Term'.apply(Factor.ast) }

Term' → '*' Factor Term'
         { Term'.apply(x) = Term'1.apply(Binary(MUL, x, Factor.ast)) }

Term' → '/' Factor Term'
         { Term'.apply(x) = Term'1.apply(Binary(DIV, x, Factor.ast)) }

Term' → ε
         { Term'.apply(x) = x }
```

#### Factores
```
Factor → '(' Exp ')'
           { Factor.ast = Exp.ast }

Factor → num
           { Factor.ast = Num(valor) }

Factor → id
           { Factor.ast = Var(id) }

Factor → '+' Factor
           { Factor.ast = Factor.ast }

Factor → '-' Factor
           { Factor.ast = Binary(SUB, Num(0), Factor.ast) }
```

---

## 📌 3. Tabla de Símbolos

La tabla de símbolos almacena:

- Nombre de la variable.
- Tipo asociado (`int` o `real`).
- Promoción automática `int → real` cuando corresponda.

Ejemplo:

```
{x:int, y:real}
```

Reglas de manejo de tipos:

- Si `int` y `real` participan en una operación → el resultado es `real`.
- Las variables adoptan el tipo del valor asignado.
- Si una variable recibe valores de distintos tipos → se promueve a `real`.

---

## 📌 4. TAC — Código en Tres Direcciones

El compilador genera código intermedio del tipo:

### ✔ Carga de constantes
```
LDCI n -> t    # entero
LDCR x -> t    # real
```

### ✔ Conversión de tipo
```
ITOR tI -> tR  # int → real
```

### ✔ Operaciones aritméticas tipadas
```
ADDI/ADDR
SUBI/SUBR
MULI/MULR
DIVI/DIVR
```

### ✔ Almacenamiento
```
STORI t -> id
STORR t -> id
```

---

## 📌 5. Ejemplo de ejecución

### Entrada:
```
>>> x = 2 + 3 * 4
```

### AST (ASCII):
```
└── Assign(x)
    └── Binary(+)
        ├── Num(2)
        └── Binary(*)
            ├── Num(3)
            └── Num(4)
```

### Tabla de Símbolos:
```
{x:int}
```

### TAC:
```
LDCI 2 -> t1
LDCI 3 -> t2
LDCI 4 -> t3
MULI t2, t3 -> t4
ADDI t1, t4 -> t5
STORI t5 -> x
```

---

## 📌 6. Ejecución

Para ejecutar el REPL:

```
python edts_python_like.py
```

Cada línea que escribas es un `Stmt` de la gramática.

---

## 📌 7. Archivos importantes

- `edts_python_like.py` → código del analizador + EDTS + TAC.
- `README.md` (este archivo).

---

## 📌 8. Conclusión

Este proyecto implementa:

- Un **analizador sintáctico LL(1)**.
- Un **EDTS completo** que genera AST.
- Una **tabla de símbolos** totalmente funcional.
- Un generador de **código intermedio TAC** realista.
- Una herramienta educativa ideal para aprender:
  ✔ análisis sintáctico  
  ✔ atributos  
  ✔ generación de código  
  ✔ estructura de compiladores  

---

Proyecto generado siguiendo las indicaciones del estudiante.
