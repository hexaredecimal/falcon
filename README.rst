Falcon
=======

Falcon is a Python-like programming language compiler and transpiler.

The project contains:

- Regular expression based lexer
- Top-down recursive descent parser
- AST-walking codegen
- REPL 
- CPP transpiler
- CPP compilation and linkage (debug symbols included)
- Static typing (missing a type checker)
- Dinamic typing (using auto, not generics)
- Built-in stdlib (no imports for Built-in functions and symbols)
- Inline C++ 


Still missing:
- Type checking 
- Type based errors
- Include files (make proper use of include files)
- Inline assembly

Falcon doesn't require any third-party libraries.

What the language looks like:

.. code-block::
    func main() -> i32:
        let fp: file = open("./loops.flc", "r")
        let buffer: string = readfile(fp)
        print(buffer)
        closefile(fp)

        return 0


.. code-block::
    func dup(x: string, count: i32) -> string:
        let result: string = ""
        for i in 1 .. count:
            result = result + x

        return result

    func main() -> i32:
        println(dup("-", 50))

        for i in 1 .. 5:
            for j in 1 .. i:
                print("*")
            println("")

You can find more examples in ``tests`` directory.

How to try it:

Requirements:
- Python 3.x.x
- GCC (with -std=c++20 support)
.. code-block::
    
    git clone https://github.com/vulture/falcon.git
    cd falcon
    make all tests
    ./test/array
    ...
