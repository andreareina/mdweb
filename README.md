

# mdweb
Not to be confused with WebMD!

*mdweb* is a tool for literate programming in Python.
It has basic support for [*noweb*](http://www.cs.tufts.edu/~nr/noweb/) syntax,
specifically *tangling* to source code,
and and *weaving* to Markdown (as opposed to LaTeX) for human consumption.

## Chunks
A *chunk* is zero or more lines of text that are either *prose* or *code*.
A prose chunk is signified by a line that starts with `@`.
A code chunk is signified by a line that starts with `<<chunk name>>=`,
where *chunk name* is the chunk's identifier.
We also need a way to refer to other code chunks within a code chunk.
They will tke the form of `<<chunk name>>` (note the absence of the "=")
and can appear anywhere in the line.
Regular expressions give us a convenient way to define these rules.

TODO: enable escaping of << and >>

**`<<patterns>>=`**

    prose_block_pat = re.compile(r"^@")
    code_block_pat = re.compile(r"^<{2}(.+)>{2}=")
    reference = re.compile(r"(.*)<{2}(.+)>{2}")



## Weaving
*Weaving* produces ready-to-publish Markdown-formatted output.
Except for code chunks, an mdweb source file is written in Markdown,
so the only thing to do is wrap code chunks in code blocks.

TODO: enable prose to begin on same line as opening "@"

**`<<weave>>=`**

    def weave(self):
        """Markdown-formatted output with code in code blocks"""
        woven = []
        mode = "prose"
        for line in self.source:
            code_match = Web.code_block_pat.match(line)
            prose_match = Web.prose_block_pat.match(line)
            if code_match:
                mode = "code"
                # Add a header to identify the block
                woven.append('**`' + line + '`**\n')
                continue
            elif prose_match:
                mode = "prose"
                woven.append('\n')
                continue
    
            if mode == "code":
                woven.append('    ' + line)
            else:
                woven.append(line)
    
        return '\n'.join(woven)



## Tangling
*Tangling* the specified root chunk expands it into the final code.
We expect the root chunk to contain references to other chunks which must be expanded,
which themselves may contain references to other chunks which must be expanded and so on.
One way to resolve the dependencies is to do a topological sort on the dependency graph and expand chunks in that order.

**`<<tangle>>=`**

    
    def __expansion_order(self, root):
        """Chunks in the order they should be processed to satisfy dependencies"""
        result = []
        visited = set()
    
        def dfs(v):
            if v not in visited:
                visited.add(v)
                for next in [e[1] for e in self.dependencies if e[0] == v]:
                    dfs(next)
                result.append(v)
    
        dfs(root)
    
        return result



Each chunk is expanded such that the substring that precedes the reference (if any) is included in every line of the expansion.
This is useful very for maintaining indentation,
especially in python where whitespace is syntactic.

We also do a little work so that undefined references
(`<<foo>>` without a corresponding `<<foo>>=`)
are simply ignored.
This lets us use them as comments which are removed in the tangled output.

**`<<tangle>>=`**

    <<No mistakes in the tango, Donna, not like life>>
    <<If you make a mistake, get all tangled up, just tango on>>
    
    def tangle(self, root):
        """Expand root into final source code"""
        expansions = {}
    
        def __expand(block):
            expansions[block] = []
            for line in self.blocks[block]:
                reference = Web.reference.match(line)
                if reference:
                    prologue, inner_block = reference.group(1, 2)
                    try:
                        for line in expansions[inner_block]:
                            # don't prepend prologue to empty lines
                            if line:
                                expansions[block].append(prologue + line)
                            else:
                                expansions[block].append(line)
                    except KeyError: # ignore undefined references
                        continue
                else:
                    expansions[block].append(line)
            if expansions[block][-1] != '':
                expansions[block].append('')
    
        for block in [x for x in self.__expansion_order(root)
                if x in self.blocks]:
            __expand(block)
    
        return '\n'.join(expansions[root])



## Finding roots
It'll be nice to get a listing of all the roots in the source.
A root is defined as a chunk that is not a dependency of any other chunk.

**`<<list roots>>=`**

    
    def roots(self):
        """List of code chunks that are not dependencies of other chunks"""
        return [block for block in self.blocks.keys()
                if block not in [edge[1] for edge in self.dependencies]]



## Putting it all together

Using a class is probably overkill for this application,
but it keeps the data nicely contained and easy to refer to.

**`<<class definition>>=`**

    class Web:
        <<patterns>>
        <<weave>>
        <<tangle>>
        <<list roots>>
        <<make graph>>
    
        def __init__(self, source):
            # source chunks and dependency graph
            self.source = source.split('\n')
            self.blocks = {} # un-tangled chunks
            self.dependencies = [] # as (chunk_name, dependency)
    
            # read in source and make dependency graph
            mode = "prose"
            for line in self.source:
                code_match = Web.code_block_pat.match(line)
                prose_match = Web.prose_block_pat.match(line)
                if code_match:
                    mode = "code"
                    block_name = code_match.group(1)
                    continue
                elif prose_match:
                    mode = "prose"
                    continue
    
                if mode == "code":
                    dependence = Web.reference.search(line)
                    if dependence:
                        self.dependencies.append((block_name, dependence.group(2)))
                    try:
                        self.blocks[block_name].append(line)
                    except KeyError:
                        self.blocks[block_name] = [line]



## Supported operations

* **tangling** `python mdweb.py --tangle <root> [file]`
* **weaving** `python mdweb.py --weave [file]`

Following the common idiom for command-line tools, if `file` is absent (or "-") `mdweb` reads from standard input.

**`<<main method>>=`**

    if __name__ == '__main__':
        import argparse
        import sys
        parser = argparse.ArgumentParser(description="Weave and tangle files")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument(
            '--list',
            action='store_true',
            help="""List top-level code blocks, one per line""",
        )
        action.add_argument(
            '--weave',
            action='store_true',
            help="""Produce markdown from input file""",
        )
        action.add_argument(
            '--tangle',
            action='store',
            metavar='root',
            help="""Tangle the named code block into code""",
        )
        parser.add_argument(
            'infile',
            type=argparse.FileType('r'),
            default=sys.stdin,
            nargs='?',
            help="Input filename; reads from standard input if absent",
        )
    
        args = parser.parse_args()
        web = Web(args.infile.read())
        if args.list:
            print('\n'.join(web.roots()))
        elif args.weave:
            print(web.weave())
        else:
            try:
                print(web.tangle(args.tangle))
            except KeyError:
                print("Source block '%s' not found" % args.tangle, file=sys.stderr)
                sys.exit(1)
        sys.exit(0)



**`<<program>>=`**

    from __future__ import print_function
    import re
    <<class definition>>
    <<main method>>



