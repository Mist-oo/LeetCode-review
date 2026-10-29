"""Versioned, line-framed EOF protocols and answer checkers for all Hot 100.

Each field consumes a known number of physical lines. In particular an empty
string occupies its own blank line and is never silently stripped/skipped.
"""
import math
from collections import Counter
from dataclasses import dataclass

from .reference import tree, serialize, traversals

VERSION = 'hot100-eof-v2.1'


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Spec:
    fields: tuple
    output: str
    details: str = ''


SPECS = {}


def define(numbers, fields, output, details=''):
    for number in numbers:
        SPECS[number] = Spec(tuple(fields), output, details)


define([1], [('nums', 'array'), ('target', 'int')], 'array', '输出两个不同的下标（从 0 开始），顺序不限。')
define([49], [('strs', 'strings')], 'string_groups', '组间、组内顺序均不限，必须完整分组且保留重复字符串。')
define([128,11,42,53,41,121,198,300,152,136,169,287,84], [('nums', 'array')], 'int')
define([283,238,206,148,75,31,739], [('nums', 'array')], 'array')
define([15,46,78], [('nums', 'array')], 'rows', '输出所有答案，不允许重复；三数之和和子集的行内顺序不限，全排列的行内顺序有意义。')
define([3,32], [('s', 'string')], 'int')
define([438], [('s', 'string'), ('p', 'string')], 'array')
define([560], [('nums', 'array'), ('k', 'int')], 'int')
define([239], [('nums', 'array'), ('k', 'int')], 'array')
define([76], [('s', 'string'), ('t', 'string')], 'string', '若有多个最短合法窗口，任一均接受；不存在时输出空行。')
define([56], [('intervals', 'pairs')], 'rows', '输出全部合并区间，区间顺序不限，每行端点必须从小到大。')
define([189], [('nums', 'array'), ('k', 'int')], 'array')
define([73,48], [('matrix', 'matrix')], 'rows', '先输出矩阵行数，再逐行输出元素。')
define([54], [('matrix', 'matrix')], 'array')
define([74,240], [('matrix', 'matrix'), ('target', 'int')], 'bool')
define([160], [('listA', 'array'), ('listB', 'array'), ('skipA', 'int'), ('skipB', 'int')], 'int', 'skipA/skipB 指向两链表共享尾部的首节点，均为 -1 表示不相交。输出交点在 listA 的 0 基下标，无交点输出 -1；相同值不代表节点相同。')
define([234], [('head', 'array')], 'bool')
define([141], [('head', 'array'), ('pos', 'int')], 'bool', 'pos 是尾节点指向的 0 基下标，-1 表示无环。')
define([142], [('head', 'array'), ('pos', 'int')], 'int', 'pos 是尾节点指向的 0 基下标，-1 表示无环。输出入环节点的 0 基下标，无环输出 -1。')
define([21,2], [('list1', 'array'), ('list2', 'array')], 'array')
define([19], [('head', 'array'), ('n', 'int')], 'array')
define([24], [('head', 'array')], 'array')
define([25], [('head', 'array'), ('k', 'int')], 'array')
define([138], [('values', 'array'), ('random', 'array')], 'two_arrays', 'random[i] 是第 i 个节点的随机指向下标，-1 为空。输出两行：新链表节点值、随机指向下标。只验证结构输出，深拷贝对象身份由自己检查。')
define([23], [('lists', 'rows')], 'array')
define([146], [('capacity', 'int'), ('operations', 'ops146')], 'array', '每条 put key value 或 get key 为一行；输出所有 get 的结果，一行用空格分隔，无 get 时输出空行。每组重新初始化缓存。')
define([94,199,114], [('root', 'tree')], 'array', '114 输出展开后的节点值序列，按右链从头到尾排列。')
define([104,543,124], [('root', 'tree')], 'int')
define([226], [('root', 'tree')], 'tree')
define([101,98], [('root', 'tree')], 'bool')
define([102], [('root', 'tree')], 'rows')
define([108], [('nums', 'array')], 'tree', '输出任一高度平衡的二叉搜索树，必须包含全部输入节点，不能输出非平衡树。')
define([230], [('root', 'tree'), ('k', 'int')], 'int')
define([105], [('preorder', 'array'), ('inorder', 'array')], 'tree')
define([437], [('root', 'tree'), ('targetSum', 'int')], 'int')
define([236], [('root', 'tree'), ('p', 'int'), ('q', 'int')], 'int', '树中节点值互不相同，p/q 是已有的两个不同节点值。输出最近公共祖先的值。')
define([200], [('grid', 'chars')], 'int')
define([994], [('grid', 'matrix')], 'int')
define([207], [('numCourses', 'int'), ('prerequisites', 'pairs')], 'bool')
define([208], [('operations', 'ops208')], 'bool_array', '操作为 insert word、search word 或 startsWith prefix，每条一行；输出所有查询的 true/false，一行空格分隔。每组重新初始化 Trie。')
define([17], [('digits', 'string')], 'strings')
define([22], [('n', 'int')], 'strings')
define([39], [('candidates', 'array'), ('target', 'int')], 'rows', '输出全部组合，组间和组内顺序不限，不允许重复组合。')
define([79], [('board', 'chars'), ('word', 'string')], 'bool')
define([131], [('s', 'string')], 'string_groups', '每一组是一种切分，组内子串顺序有意义，必须列出所有不重复的回文切分。')
define([51], [('n', 'int')], 'boards', '先输出方案数 k，再输出 k 个棋盘；每个棋盘固定 n 行，每行 n 个字符。必须列出全部不重复的解，方案间不加空行。')
define([35,33], [('nums', 'array'), ('target', 'int')], 'int')
define([34], [('nums', 'array'), ('target', 'int')], 'array')
define([153], [('nums', 'array')], 'int')
define([4], [('nums1', 'array'), ('nums2', 'array')], 'float')
define([20], [('s', 'string')], 'bool')
define([155], [('operations', 'ops155')], 'array', 'push x、pop、top、getMin，每条一行，只输出 top/getMin 的结果，空格分隔。输入保证不会对空栈执行查询或 pop。')
define([394], [('s', 'string')], 'string')
define([347], [('nums', 'array'), ('k', 'int')], 'array')
define([215], [('nums', 'array'), ('k', 'int')], 'int')
define([295], [('operations', 'ops295')], 'float_array', 'addNum x 或 findMedian，每条一行，只输出 findMedian 结果，空格分隔。查询时至少已有一个数。')
define([55,416], [('nums', 'array')], 'bool')
define([45], [('nums', 'array')], 'int')
define([763], [('s', 'string')], 'array')
define([70,279], [('n', 'int')], 'int')
define([118], [('numRows', 'int')], 'rows')
define([322], [('coins', 'array'), ('amount', 'int')], 'int')
define([139], [('s', 'string'), ('wordDict', 'strings')], 'bool')
define([62], [('m', 'int'), ('n', 'int')], 'int')
define([64], [('grid', 'matrix')], 'int')
define([5], [('s', 'string')], 'string', '输出任意一个最长回文子串；同样长度的不同合法答案都接受。')
define([1143,72], [('text1', 'string'), ('text2', 'string')], 'int')

FIELD_HELP = {
    'int': '一行一个整数。',
    'array': '一行长度 n，下一行恰好 n 个空格分隔的整数；n=0 时仍保留下一空行。',
    'string': '一行字符数 n，下一行原始字符串（不去掉空格）；n=0 时下一行为空行。',
    'strings': '一行字符串个数 n，随后 n 个字符串，每个先一行长度，再一行内容（允许空字符串）。',
    'pairs': '一行记录数 n，随后 n 行，每行两个整数。',
    'matrix': '一行 m n，随后 m 行，每行 n 个空格分隔的整数。',
    'chars': '一行 m n，随后 m 行，每行连续 n 个字符，不加空格。',
    'tree': '一行层序槽位数 k，下一行恰好 k 个空格分隔值；空节点写 null。k=0 时保留空行。采用队列层序，空节点不再分配子槽位。',
    'rows': '一行链表条数 k，每条先一行长度 n，再一行 n 个整数（空链表也保留空行）。',
    'ops146': '一行操作条数 q，随后 q 行 put key value 或 get key。',
    'ops155': '一行操作条数 q，随后 q 行 push x、pop、top 或 getMin。',
    'ops208': '一行操作条数 q，随后 q 行 insert word、search word 或 startsWith word。word 为非空小写字母串。',
    'ops295': '一行操作条数 q，随后 q 行 addNum x 或 findMedian。',
}
OUTPUT_HELP = {
    'int': '每组输出一行整数。', 'float': '每组输出一行数值，允许 1e-5 的绝对或相对误差。',
    'bool': '每组输出一行 true 或 false（不区分大小写）。',
    'string': '每组输出一行原始字符串；空答案也必须输出空行。',
    'array': '每组输出一行空格分隔的整数，不写长度；空数组输出空行。',
    'bool_array': '每组输出一行空格分隔的 true/false；没有查询时输出空行。',
    'float_array': '每组输出一行空格分隔的数值，允许 1e-5 绝对或相对误差；没有查询时输出空行。',
    'rows': '每组先输出一行答案行数 k，再输出 k 行整数序列（不写每行长度，空序列保留空行）。',
    'strings': '每组先输出一行答案个数 k，再输出 k 行字符串；空字符串保留空行。',
    'string_groups': '每组先输出分组/方案数 k；每个分组先一行成员数 m，再输出 m 行原始字符串（空字符串保留空行）。',
    'two_arrays': '每组输出两行整数数组，不写长度；分别是节点值和 random 下标。',
    'tree': '每组输出一行空格分隔的层序值，空节点用 null，允许省略末尾 null；空树输出 null。',
    'boards': '每组先输出方案数 k，再输出 k 个 n 行棋盘，每行仅由 . 和 Q 组成。',
}


class Lines:
    def __init__(self, source):
        self.lines, self.index = source.replace('\r\n', '\n').splitlines(), 0

    def line(self):
        if self.index >= len(self.lines):
            raise ProtocolError('数据提前结束，请保留空字符串/空数组应有的空行')
        result = self.lines[self.index]
        self.index += 1
        return result

    def integer(self):
        parts = self.line().split()
        if len(parts) != 1:
            raise ProtocolError('应为一行一个整数')
        return int(parts[0])

    def remaining(self):
        return len(self.lines) - self.index


def size(value, maximum=500_000):
    if not 0 <= value <= maximum:
        raise ProtocolError(f'长度或条数应在 0 到 {maximum} 范围内')
    return value


def read_field(reader, kind):
    if kind == 'int':
        return reader.integer()
    if kind in ('array', 'tree'):
        n = size(reader.integer())
        words = reader.line().split()
        if len(words) != n:
            raise ProtocolError('声明的数组/树长度与元素个数不同')
        return [None if kind == 'tree' and word == 'null' else int(word) for word in words]
    if kind == 'string':
        n, value = size(reader.integer()), reader.line()
        if len(value) != n:
            raise ProtocolError('声明的字符串长度与字符数不同')
        return value
    if kind in ('strings', 'rows'):
        return [read_field(reader, 'string' if kind == 'strings' else 'array') for _ in range(size(reader.integer(), 30_000))]
    if kind == 'pairs':
        result = []
        for _ in range(size(reader.integer(), 100_000)):
            row = [int(x) for x in reader.line().split()]
            if len(row) != 2:
                raise ProtocolError('每行必须恰好两个整数')
            result.append(row)
        return result
    if kind in ('matrix', 'chars'):
        dims = [int(x) for x in reader.line().split()]
        if len(dims) != 2 or not all(1 <= d <= 1000 for d in dims) or dims[0] * dims[1] > 1_000_000:
            raise ProtocolError('矩阵尺寸无效')
        m, n = dims
        rows = [list(reader.line()) if kind == 'chars' else [int(x) for x in reader.line().split()] for _ in range(m)]
        if any(len(row) != n for row in rows):
            raise ProtocolError('矩阵行长与列数不同')
        return rows
    if kind.startswith('ops'):
        operations, signatures = [], {
            'ops146': {'put':2, 'get':1}, 'ops155': {'push':1, 'pop':0, 'top':0, 'getMin':0},
            'ops208': {'insert':1, 'search':1, 'startsWith':1}, 'ops295': {'addNum':1, 'findMedian':0}}[kind]
        for _ in range(size(reader.integer(), 200_000)):
            parts = reader.line().split()
            if not parts or parts[0] not in signatures or len(parts) != signatures[parts[0]] + 1:
                raise ProtocolError('操作名称或参数个数不正确')
            operations.append(parts if kind == 'ops208' else [parts[0], *map(int, parts[1:])])
        return operations
    raise ProtocolError(f'未知输入类型 {kind}')


def encode_field(kind, value):
    if kind == 'int':
        return f'{value}\n'
    if kind in ('array', 'tree'):
        return f'{len(value)}\n' + ' '.join('null' if x is None else str(x) for x in value) + '\n'
    if kind == 'string':
        return f'{len(value)}\n{value}\n'
    if kind in ('strings', 'rows'):
        return f'{len(value)}\n' + ''.join(encode_field('string' if kind == 'strings' else 'array', row) for row in value)
    if kind == 'pairs':
        return f'{len(value)}\n' + ''.join(' '.join(map(str, row)) + '\n' for row in value)
    if kind in ('matrix', 'chars'):
        return f'{len(value)} {len(value[0])}\n' + ''.join(('' if kind == 'chars' else ' ').join(map(str, row)) + '\n' for row in value)
    return f'{len(value)}\n' + ''.join(' '.join(map(str, row)) + '\n' for row in value)


def encode_case(number, args):
    return ''.join(encode_field(kind, value) for (_, kind), value in zip(SPECS[number].fields, args))


def decode_cases(number, source):
    reader, cases = Lines(source), []
    try:
        while reader.remaining():
            # EOF is the only terminator; blank lines are not extra separators.
            args = [read_field(reader, kind) for name, kind in SPECS[number].fields]
            cases.append(args)
            if len(cases) > 5000:
                raise ProtocolError('一次最多运行 5000 组')
        if not cases:
            raise ProtocolError('至少输入一组完整数据')
        return cases
    except (ValueError, IndexError) as error:
        raise ProtocolError(f'第 {len(cases) + 1} 组输入格式错误：{error}') from error


def encode_answer(number, answer):
    kind = SPECS[number].output
    if kind == 'bool':
        return ('true' if answer else 'false') + '\n'
    if kind in ('int', 'float', 'string'):
        return str(answer) + '\n'
    if kind in ('array', 'float_array', 'bool_array', 'tree'):
        if kind == 'tree' and not answer:
            return 'null\n'
        return ' '.join('null' if x is None else ('true' if x else 'false') if isinstance(x, bool) else str(x) for x in answer) + '\n'
    if kind == 'two_arrays':
        return ''.join(' '.join(map(str, row)) + '\n' for row in answer)
    if kind == 'rows':
        return str(len(answer)) + '\n' + ''.join(' '.join(map(str, row)) + '\n' for row in answer)
    if kind == 'strings':
        return str(len(answer)) + '\n' + ''.join(s + '\n' for s in answer)
    if kind == 'string_groups':
        return str(len(answer)) + '\n' + ''.join(str(len(row)) + '\n' + ''.join(s + '\n' for s in row) for row in answer)
    if kind == 'boards':
        return str(len(answer)) + '\n' + ''.join(s + '\n' for board in answer for s in board)
    raise ProtocolError('未知输出类型')


def boolean(value):
    if value.lower() not in ('true', 'false'):
        raise ProtocolError('布尔输出必须是 true/false')
    return value.lower() == 'true'


def read_answer(number, args, reader):
    kind = SPECS[number].output
    if kind in ('int', 'float', 'bool', 'string'):
        line = reader.line()
        if kind == 'string':
            return line
        parts = line.split()
        if len(parts) != 1:
            raise ProtocolError('每组应输出一行一个结果')
        return {'int': int, 'float': float, 'bool': boolean}[kind](parts[0])
    if kind in ('array', 'float_array', 'bool_array', 'tree'):
        words = reader.line().split()
        if kind == 'tree':
            return [None if word == 'null' else int(word) for word in words]
        return [{'array': int, 'float_array': float, 'bool_array': boolean}[kind](word) for word in words]
    if kind == 'two_arrays':
        return [[int(word) for word in reader.line().split()] for _ in range(2)]
    count = size(reader.integer(), 100_000)
    if kind == 'rows':
        return [[int(word) for word in reader.line().split()] for _ in range(count)]
    if kind == 'strings':
        return [reader.line() for _ in range(count)]
    if kind == 'string_groups':
        return [[reader.line() for _ in range(size(reader.integer(), 100_000))] for _ in range(count)]
    if kind == 'boards':
        return [[reader.line() for _ in range(args[0])] for _ in range(count)]
    raise ProtocolError('未知输出类型')


def normalize_rows(rows, sort_inside=False):
    return Counter(tuple(sorted(row)) if sort_inside else tuple(row) for row in rows)


def accepts(number, args, actual, expected):
    if number == 1:
        return len(actual) == 2 and len(set(actual)) == 2 and all(0 <= i < len(args[0]) for i in actual) and sum(args[0][i] for i in actual) == args[1]
    if number == 5:
        return actual == actual[::-1] and actual in args[0] and len(actual) == len(expected)
    if number == 76:
        return len(actual) == len(expected) and actual in args[0] and (not expected or not Counter(args[1]) - Counter(actual))
    if number == 347:
        counts, k = Counter(args[0]), args[1]
        if len(actual) != k or len(set(actual)) != k or any(x not in counts for x in actual):
            return False
        return min(counts[x] for x in actual) >= max((count for x, count in counts.items() if x not in actual), default=0)
    if number == 108:
        try:
            root = tree(actual)
            if traversals(root)[1] != args[0]:
                return False
            heights, stack = {}, [(root, False)]
            while stack:
                node, visited = stack.pop()
                if not node:
                    continue
                if not visited:
                    stack.extend([(node, True), (node.left, False), (node.right, False)])
                else:
                    l, r = heights.get(node.left, 0), heights.get(node.right, 0)
                    if abs(l - r) > 1:
                        return False
                    heights[node] = 1 + max(l, r)
            return True
        except (ValueError, IndexError):
            return False
    if number in (226, 105):
        try:
            return serialize(tree(actual)) == expected
        except ValueError:
            return False
    if number in (15, 39, 78, 46, 56, 49, 131, 51):
        sort_inside = number in (15, 39, 78, 49)
        value = normalize_rows(actual, sort_inside)
        return all(count == 1 for count in value.values()) and value == normalize_rows(expected, sort_inside)
    if number in (17, 22):
        return len(actual) == len(set(actual)) and Counter(actual) == Counter(expected)
    if number in (4, 295):
        left, right = ([actual], [expected]) if number == 4 else (actual, expected)
        return len(left) == len(right) and all(math.isfinite(x) and math.isclose(x, y, rel_tol=1e-5, abs_tol=1e-5) for x, y in zip(left, right))
    return actual == expected


def judge_output(number, cases, expected, source):
    reader, results = Lines(source), []
    for args, answer in zip(cases, expected):
        try:
            actual = read_answer(number, args, reader)
            results.append(dict(ok=bool(accepts(number, args, actual, answer)), actual=actual, error=''))
        except (ValueError, IndexError) as error:
            results.append(dict(ok=False, actual=None, error=str(error)))
            # A malformed variable-length result loses framing: remaining groups
            # are unverified, not guessed as passed by substring alignment.
            results.extend(dict(ok=False, actual=None, error='此前输出格式错误，无法定位本组边界') for _ in range(len(cases) - len(results)))
            break
    if reader.remaining() and any(line.strip() for line in reader.lines[reader.index:]):
        if results:
            results[-1].update(ok=False, error='全部结果之后仍有多余输出')
    return results


def public_spec(number):
    spec = SPECS[number]
    return dict(version=VERSION,
                introduction='多组数据直到 EOF，不含 T。按下列字段顺序重复读取每组；不要在组间额外插入空行。',
                fields=[dict(name=name, kind=kind, description=FIELD_HELP[kind]) for name, kind in spec.fields],
                output=OUTPUT_HELP[spec.output], details=spec.details,
                limits=dict(batch_seconds=3, memory_mb=256, output_mb=16))
