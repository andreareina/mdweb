from __future__ import print_function
import re
class Web:
    prose_block_pat = re.compile(r"^@")
    code_block_pat = re.compile(r"^<{2}(.+)>{2}=")
    reference = re.compile(r"(.*)<{2}(.+)>{2}")

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


    def roots(self):
        return [block for blocks in self.blocks.keys()
                if block not in [edge[1] for edge in self.dependencies]]


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

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Weave and tangle files")
    action = parser.add_mutually_exclusive_group(required=True)
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
    if args.weave:
        print(web.weave())
        sys.exit(0)
    else:
        print(web.tangle(args.tangle))
        sys.exit(0)

