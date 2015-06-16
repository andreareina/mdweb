import sys, re

class Web:
    prose_block_pat = re.compile(r"^@")
    code_block_pat = re.compile(r"^<{2}(.+)>{2}=")
    reference = re.compile(r"(.*)<{2}(.+)>{2}")
    
    def weave(self):
        woven = []
        mode = "prose"
        for line in self.source:
            code_match = Web.code_block_pat.match(line)
            prose_match = Web.prose_block_pat.match(line)
            if code_match:
                mode = "code"
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
    
    def __init__(self, source):
        self.source = source.split('\n')
        self.blocks = {}
        self.dependencies = []
        self.__make_dag()
        self.roots = [block for block in self.blocks.keys() if block not in
                      [edge[1] for edge in self.dependencies]]
    
    def __make_dag(self):
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
    
    def __expansion_order(self, target):
        """Blocks in the order they should be processed to satisfy dependencies"""
        result = []
        visited = set()
    
        def dfs(v):
            if v not in visited:
                for next in [e[1] for e in self.dependencies if e[0] == v]:
                    dfs(next)
                visited.add(v)
                result.append(v)
    
        dfs(target)
    
        return result
    
    def tangle(self, root):
        expansions = {}
    
        def __expand(block):
            expansions[block] = []
            for line in self.blocks[block]:
                reference = Web.reference.match(line)
                if reference:
                    prologue, inner_block = reference.group(1, 2)
                    try:
                        for line in expansions[inner_block]:
                            expansions[block].append(prologue + line)
                    except KeyError:
                        continue
                else:
                    expansions[block].append(line)
            if expansions[block][-1] != '':
                expansions[block].append('')
    
        for block in [x for x in self.__expansion_order(root) if x in self.blocks]:
            __expand(block)
    
        return '\n'.join(expansions[root])
    

if __name__ == '__main__':
    help_options = ['-?', '--help']
    options = ['--tangle', '--weave'] + help_options
    usage_message = """Usage: mdweb <--tangle [root] | --weave> <file>"""

    def call_error():
        print usage_message
        sys.exit(1)

    if len(sys.argv) < 2 or sys.argv[1] not in options:
        call_error()
    elif sys.argv[1] in help_options:
        print usage_message
        sys.exit(0)

    file = sys.argv[-1]
    action = sys.argv[1]
    with open(file, 'r') as f:
        web = Web(f.read())
        if action == '--weave':
            print web.weave()
            sys.exit(0)
        elif action == '--tangle':
            if len(sys.argv) != 3:
                root = sys.argv[2]
            else:
                root = '*'

            print web.tangle(root)
