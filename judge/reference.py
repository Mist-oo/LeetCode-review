"""Trusted reference computations on canonical values, not student code.

Deliberately independent of stdin/stdout codecs so protocol roundtrips and
small-instance differential oracles can test the two layers separately.
"""
from bisect import bisect_left, bisect_right
from collections import Counter, OrderedDict, defaultdict, deque
from functools import lru_cache
from heapq import heappush, heappop
from itertools import permutations
from math import comb, isqrt


class Node:
    def __init__(self, value):
        self.value, self.left, self.right = value, None, None


def tree(values):
    if not values:
        return None
    if values[0] is None:
        if any(value is not None for value in values):
            raise ValueError('空根节点后不能出现非空节点')
        return None
    root = Node(values[0])
    queue, index = deque([root]), 1
    while queue and index < len(values):
        node = queue.popleft()
        for side in ('left', 'right'):
            if index == len(values):
                break
            value = values[index]
            index += 1
            if value is not None:
                child = Node(value)
                setattr(node, side, child)
                queue.append(child)
    if index != len(values):
        raise ValueError('不可达的层序节点')
    return root


def serialize(root):
    if root is None:
        return []
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.value if node else None)
        if node:
            queue.extend([node.left, node.right])
    while result and result[-1] is None:
        result.pop()
    return result


def traversals(root):
    pre, ino, post, stack = [], [], [], [(root, 0)]
    while stack:
        node, action = stack.pop()
        if node is None:
            continue
        if action == 0:
            pre.append(node.value)
            stack.extend([(node, 2), (node.right, 0), (node, 1), (node.left, 0)])
        elif action == 1:
            ino.append(node.value)
        else:
            post.append(node.value)
    return pre, ino, post


def solve(number, args):
    """Compute one canonical answer. Multi-answer acceptance is in the checker."""
    a = args[0]
    if number == 1:
        seen = {}
        for i, x in enumerate(a):
            if args[1] - x in seen:
                return [seen[args[1] - x], i]
            seen[x] = i
        raise ValueError('两数之和必须存在解')
    if number == 49:
        groups = defaultdict(list)
        for s in a:
            groups[''.join(sorted(s))].append(s)
        return list(groups.values())
    if number == 128:
        values, best = set(a), 0
        for x in values:
            if x - 1 not in values:
                y = x
                while y in values:
                    y += 1
                best = max(best, y - x)
        return best
    if number == 283:
        nonzero = [x for x in a if x]
        return nonzero + [0] * (len(a) - len(nonzero))
    if number == 11:
        i, j, best = 0, len(a) - 1, 0
        while i < j:
            best = max(best, min(a[i], a[j]) * (j - i))
            if a[i] < a[j]:
                i += 1
            else:
                j -= 1
        return best
    if number == 15:
        values, result = sorted(a), []
        for i in range(len(values) - 2):
            if i and values[i] == values[i - 1]:
                continue
            l, r = i + 1, len(values) - 1
            while l < r:
                total = values[i] + values[l] + values[r]
                if total < 0:
                    l += 1
                elif total > 0:
                    r -= 1
                else:
                    result.append([values[i], values[l], values[r]])
                    l += 1
                    r -= 1
                    while l < r and values[l] == values[l - 1]:
                        l += 1
        return result
    if number == 42:
        left, right, lm, rm, water = 0, len(a) - 1, 0, 0, 0
        while left <= right:
            if lm <= rm:
                lm = max(lm, a[left]); water += lm - a[left]; left += 1
            else:
                rm = max(rm, a[right]); water += rm - a[right]; right -= 1
        return water
    if number == 3:
        seen, start, best = {}, 0, 0
        for i, c in enumerate(a):
            start = max(start, seen.get(c, -1) + 1)
            seen[c] = i
            best = max(best, i - start + 1)
        return best
    if number == 438:
        s, p = args
        need, current, result = Counter(p), Counter(), []
        for i, c in enumerate(s):
            current[c] += 1
            if i >= len(p):
                current[s[i - len(p)]] -= 1
                if current[s[i - len(p)]] == 0:
                    del current[s[i - len(p)]]
            if current == need:
                result.append(i - len(p) + 1)
        return result
    if number == 560:
        counts, total, result = Counter({0: 1}), 0, 0
        for x in a:
            total += x
            result += counts[total - args[1]]
            counts[total] += 1
        return result
    if number == 239:
        q, result, k = deque(), [], args[1]
        for i, x in enumerate(a):
            while q and q[0] <= i - k:
                q.popleft()
            while q and a[q[-1]] <= x:
                q.pop()
            q.append(i)
            if i >= k - 1:
                result.append(a[q[0]])
        return result
    if number == 76:
        s, t = args
        need, missing, left, best = Counter(t), len(t), 0, (0, len(s) + 1)
        for right, c in enumerate(s, 1):
            missing -= need[c] > 0
            need[c] -= 1
            if missing == 0:
                while need[s[left]] < 0:
                    need[s[left]] += 1; left += 1
                if right - left < best[1] - best[0]:
                    best = left, right
                need[s[left]] += 1; missing += 1; left += 1
        return '' if best[1] > len(s) else s[best[0]:best[1]]
    if number == 53:
        best = running = a[0]
        for x in a[1:]:
            running = max(x, running + x); best = max(best, running)
        return best
    if number == 56:
        result = []
        for l, r in sorted(a):
            if result and l <= result[-1][1]:
                result[-1][1] = max(result[-1][1], r)
            else:
                result.append([l, r])
        return result
    if number == 189:
        k = args[1] % len(a)
        return a[-k:] + a[:-k] if k else list(a)
    if number == 238:
        result, value = [1] * len(a), 1
        for i, x in enumerate(a):
            result[i] = value; value *= x
        value = 1
        for i in range(len(a) - 1, -1, -1):
            result[i] *= value; value *= a[i]
        return result
    if number == 41:
        values, result = set(a), 1
        while result in values:
            result += 1
        return result
    if number == 73:
        rows = {i for i, row in enumerate(a) if 0 in row}
        cols = {j for row in a for j, value in enumerate(row) if value == 0}
        return [[0 if i in rows or j in cols else value for j, value in enumerate(row)] for i, row in enumerate(a)]
    if number == 54:
        matrix, result = [row[:] for row in a], []
        while matrix:
            result.extend(matrix.pop(0))
            if matrix and matrix[0]:
                matrix = [list(row) for row in zip(*matrix)][::-1]
        return result
    if number == 48:
        return [list(row) for row in zip(*a[::-1])]
    if number in (74, 240):
        i, j = 0, len(a[0]) - 1
        while i < len(a) and j >= 0:
            if a[i][j] == args[1]:
                return True
            if a[i][j] > args[1]:
                j -= 1
            else:
                i += 1
        return False
    if number == 160:
        return args[2] if args[2] >= 0 else -1
    if number == 206:
        return a[::-1]
    if number == 234:
        return a == a[::-1]
    if number == 141:
        return args[1] >= 0
    if number == 142:
        return args[1]
    if number in (21, 23):
        return sorted(a + args[1]) if number == 21 else sorted(x for row in a for x in row)
    if number == 2:
        left, right, carry, result = a, args[1], 0, []
        for i in range(max(len(left), len(right))):
            carry += (left[i] if i < len(left) else 0) + (right[i] if i < len(right) else 0)
            result.append(carry % 10); carry //= 10
        if carry:
            result.append(carry)
        return result
    if number == 19:
        index = len(a) - args[1]
        return a[:index] + a[index + 1:]
    if number in (24, 25):
        result, k = list(a), 2 if number == 24 else args[1]
        for start in range(0, len(a) - k + 1, k):
            result[start:start + k] = reversed(result[start:start + k])
        return result
    if number == 138:
        return [a[:], args[1][:]]
    if number == 148:
        return sorted(a)
    if number == 146:
        cache, result = OrderedDict(), []
        for op in args[1]:
            if op[0] == 'get':
                result.append(cache.get(op[1], -1))
                if op[1] in cache:
                    cache.move_to_end(op[1])
            else:
                cache[op[1]] = op[2]; cache.move_to_end(op[1])
                if len(cache) > a:
                    cache.popitem(last=False)
        return result
    if number in (94, 104, 226, 101, 543, 102, 108, 98, 230, 199, 114, 437, 236, 124):
        root = tree(a) if number != 108 else None
        if number == 108:
            def build(l, r):
                if l >= r:
                    return None
                m = (l + r) // 2
                node = Node(a[m]); node.left = build(l, m); node.right = build(m + 1, r)
                return node
            return serialize(build(0, len(a)))
        if number == 94:
            return traversals(root)[1]
        if number in (104, 102, 199):
            levels, queue = [], deque([root] if root else [])
            while queue:
                row = []
                for _ in range(len(queue)):
                    node = queue.popleft(); row.append(node.value)
                    queue.extend(c for c in (node.left, node.right) if c)
                levels.append(row)
            return len(levels) if number == 104 else (levels if number == 102 else [row[-1] for row in levels])
        if number == 226:
            stack = [root] if root else []
            while stack:
                node = stack.pop(); node.left, node.right = node.right, node.left
                stack.extend(c for c in (node.left, node.right) if c)
            return serialize(root)
        if number == 101:
            queue = deque([(root.left, root.right)] if root else [])
            while queue:
                x, y = queue.popleft()
                if not x or not y:
                    if x is not y:
                        return False
                    continue
                if x.value != y.value:
                    return False
                queue.extend([(x.left, y.right), (x.right, y.left)])
            return True
        if number == 98:
            values = traversals(root)[1]
            return all(values[i] < values[i + 1] for i in range(len(values) - 1))
        if number == 230:
            return traversals(root)[1][args[1] - 1]
        if number == 114:
            return traversals(root)[0]
        if number == 236:
            parents, nodes, stack = {root: None}, {}, [root]
            while stack:
                node = stack.pop(); nodes[node.value] = node
                for child in (node.left, node.right):
                    if child:
                        parents[child] = node; stack.append(child)
            x, y, ancestors = nodes[args[1]], nodes[args[2]], set()
            while x:
                ancestors.add(x); x = parents[x]
            while y not in ancestors:
                y = parents[y]
            return y.value
        if number == 437:
            counts, result, stack = Counter({0: 1}), 0, [(root, 0, False)]
            while stack:
                node, prefix, exiting = stack.pop()
                if node is None:
                    continue
                if exiting:
                    counts[prefix] -= 1
                    continue
                prefix += node.value; result += counts[prefix - args[1]]; counts[prefix] += 1
                stack.extend([(node, prefix, True), (node.right, prefix, False), (node.left, prefix, False)])
            return result
        best, values, stack = (-10 ** 30 if number == 124 else 0), {}, [(root, False)]
        while stack:
            node, visited = stack.pop()
            if node is None:
                continue
            if not visited:
                stack.extend([(node, True), (node.right, False), (node.left, False)])
            else:
                l, r = values.get(node.left, 0), values.get(node.right, 0)
                if number == 543:
                    best = max(best, l + r); values[node] = 1 + max(l, r)
                else:
                    l, r = max(0, l), max(0, r)
                    best = max(best, node.value + l + r); values[node] = node.value + max(l, r)
        return best
    if number == 105:
        pre, ino = args
        if not pre:
            return []
        root, stack, i = Node(pre[0]), [], 0
        stack.append(root)
        for value in pre[1:]:
            node = stack[-1]
            if node.value != ino[i]:
                node.left = Node(value); stack.append(node.left)
            else:
                while stack and stack[-1].value == ino[i]:
                    node = stack.pop(); i += 1
                node.right = Node(value); stack.append(node.right)
        return serialize(root)
    if number == 200:
        seen, result = set(), 0
        for i in range(len(a)):
            for j in range(len(a[0])):
                if a[i][j] == '0' or (i, j) in seen:
                    continue
                result += 1; stack = [(i, j)]; seen.add((i, j))
                while stack:
                    x, y = stack.pop()
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < len(a) and 0 <= ny < len(a[0]) and a[nx][ny] == '1' and (nx, ny) not in seen:
                            seen.add((nx, ny)); stack.append((nx, ny))
        return result
    if number == 994:
        grid, fresh, queue = [row[:] for row in a], sum(row.count(1) for row in a), deque()
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                if v == 2:
                    queue.append((i, j, 0))
        time = 0
        while queue:
            x, y, time = queue.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(a) and 0 <= ny < len(a[0]) and grid[nx][ny] == 1:
                    fresh -= 1; grid[nx][ny] = 2; queue.append((nx, ny, time + 1))
        return -1 if fresh else time
    if number == 207:
        edges, counts = [[] for _ in range(a)], [0] * a
        for course, prerequisite in args[1]:
            edges[prerequisite].append(course); counts[course] += 1
        queue = deque(i for i, count in enumerate(counts) if not count)
        visited = 0
        while queue:
            visited += 1
            for target in edges[queue.popleft()]:
                counts[target] -= 1
                if not counts[target]:
                    queue.append(target)
        return visited == a
    if number == 208:
        root, result = {}, []
        for command, word in a:
            node = root
            if command == 'insert':
                for c in word:
                    node = node.setdefault(c, {})
                node['$'] = True
            else:
                for c in word:
                    node = node.get(c)
                    if node is None:
                        break
                result.append(node is not None and (command == 'startsWith' or '$' in node))
        return result
    if number == 46:
        return [list(p) for p in permutations(a)]
    if number == 78:
        result = [[]]
        for x in a:
            result += [row + [x] for row in result]
        return result
    if number == 17:
        if not a:
            return []
        result = ['']
        for digit in a:
            result = [prefix + c for prefix in result for c in {'2':'abc','3':'def','4':'ghi','5':'jkl','6':'mno','7':'pqrs','8':'tuv','9':'wxyz'}[digit]]
        return result
    if number == 39:
        result, values = [], sorted(a)
        def visit(index, remaining, path):
            if remaining == 0:
                result.append(path[:]); return
            for i in range(index, len(values)):
                if values[i] > remaining:
                    break
                visit(i, remaining - values[i], path + [values[i]])
        visit(0, args[1], [])
        return result
    if number == 22:
        result = []
        def visit(s, l, r):
            if r == a:
                result.append(s); return
            if l < a:
                visit(s + '(', l + 1, r)
            if r < l:
                visit(s + ')', l, r + 1)
        visit('', 0, 0)
        return result
    if number == 79:
        word, m, n = args[1], len(a), len(a[0])
        if Counter(word) - Counter(c for row in a for c in row):
            return False
        def visit(x, y, index, seen):
            if a[x][y] != word[index]:
                return False
            if index == len(word) - 1:
                return True
            seen.add((x, y))
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < m and 0 <= ny < n and (nx, ny) not in seen and visit(nx, ny, index + 1, seen):
                    seen.remove((x, y)); return True
            seen.remove((x, y)); return False
        return any(visit(i, j, 0, set()) for i in range(m) for j in range(n))
    if number == 131:
        result = []
        def visit(start, path):
            if start == len(a):
                result.append(path); return
            for end in range(start + 1, len(a) + 1):
                s = a[start:end]
                if s == s[::-1]:
                    visit(end, path + [s])
        visit(0, [])
        return result
    if number == 51:
        result = []
        def visit(cols, diag1, diag2, path):
            row = len(path)
            if row == a:
                result.append(['.' * c + 'Q' + '.' * (a - c - 1) for c in path]); return
            for col in range(a):
                if col not in cols and row - col not in diag1 and row + col not in diag2:
                    visit(cols | {col}, diag1 | {row - col}, diag2 | {row + col}, path + [col])
        visit(set(), set(), set(), [])
        return result
    if number == 35:
        return bisect_left(a, args[1])
    if number == 34:
        l, r = bisect_left(a, args[1]), bisect_right(a, args[1])
        return [l, r - 1] if l < r else [-1, -1]
    if number == 33:
        target, l, r = args[1], 0, len(a) - 1
        while l <= r:
            m = (l + r) // 2
            if a[m] == target:
                return m
            if a[l] <= a[m]:
                if a[l] <= target < a[m]:
                    r = m - 1
                else:
                    l = m + 1
            elif a[m] < target <= a[r]:
                l = m + 1
            else:
                r = m - 1
        return -1
    if number == 153:
        l, r = 0, len(a) - 1
        while l < r:
            m = (l + r) // 2
            if a[m] > a[r]:
                l = m + 1
            else:
                r = m
        return a[l]
    if number == 4:
        x, y = args
        if len(x) > len(y):
            x, y = y, x
        l, r, half = 0, len(x), (len(x) + len(y) + 1) // 2
        while l <= r:
            i = (l + r) // 2; j = half - i
            xl, xr = (x[i - 1] if i else -float('inf')), (x[i] if i < len(x) else float('inf'))
            yl, yr = (y[j - 1] if j else -float('inf')), (y[j] if j < len(y) else float('inf'))
            if xl > yr:
                r = i - 1
            elif yl > xr:
                l = i + 1
            else:
                return max(xl, yl) if (len(x) + len(y)) % 2 else (max(xl, yl) + min(xr, yr)) / 2
    if number == 20:
        stack, pairs = [], {')':'(', ']':'[', '}':'{'}
        for c in a:
            if c in '([{':
                stack.append(c)
            elif not stack or stack.pop() != pairs[c]:
                return False
        return not stack
    if number == 155:
        stack, minimum, result = [], [], []
        for op in a:
            if op[0] == 'push':
                stack.append(op[1]); minimum.append(min(op[1], minimum[-1] if minimum else op[1]))
            elif op[0] == 'pop':
                stack.pop(); minimum.pop()
            elif op[0] == 'top':
                result.append(stack[-1])
            else:
                result.append(minimum[-1])
        return result
    if number == 394:
        stack, count, result = [], 0, ''
        for c in a:
            if c.isdigit():
                count = count * 10 + int(c)
            elif c == '[':
                stack.append((result, count)); result, count = '', 0
            elif c == ']':
                previous, count = stack.pop(); result = previous + count * result; count = 0
            else:
                result += c
        return result
    if number == 739:
        stack, result = [], [0] * len(a)
        for i, x in enumerate(a):
            while stack and a[stack[-1]] < x:
                j = stack.pop(); result[j] = i - j
            stack.append(i)
        return result
    if number == 84:
        stack, best, heights = [], 0, list(a) + [0]
        for i, x in enumerate(heights):
            while stack and heights[stack[-1]] > x:
                height = heights[stack.pop()]; best = max(best, height * (i - (stack[-1] if stack else -1) - 1))
            stack.append(i)
        return best
    if number == 215:
        return sorted(a)[-args[1]]
    if number == 347:
        return [x for x, count in Counter(a).most_common(args[1])]
    if number == 295:
        low, high, result = [], [], []
        for op in a:
            if op[0] == 'addNum':
                heappush(low, -op[1]); heappush(high, -heappop(low))
                if len(high) > len(low):
                    heappush(low, -heappop(high))
            else:
                result.append(-low[0] if len(low) > len(high) else (high[0] - low[0]) / 2)
        return result
    if number == 121:
        minimum, best = float('inf'), 0
        for x in a:
            minimum = min(minimum, x); best = max(best, x - minimum)
        return best
    if number in (55, 45):
        reach, end, jumps = 0, 0, 0
        for i, x in enumerate(a[:-1]):
            if i > reach:
                return False
            reach = max(reach, i + x)
            if i == end:
                jumps += 1; end = reach
        return reach >= len(a) - 1 if number == 55 else jumps
    if number == 763:
        ends, result, start, end = {c: i for i, c in enumerate(a)}, [], 0, 0
        for i, c in enumerate(a):
            end = max(end, ends[c])
            if i == end:
                result.append(end - start + 1); start = end + 1
        return result
    if number == 70:
        x, y = 1, 1
        for _ in range(a):
            x, y = y, x + y
        return x
    if number == 118:
        result = []
        for i in range(a):
            row = [1] * (i + 1)
            for j in range(1, i):
                row[j] = result[-1][j - 1] + result[-1][j]
            result.append(row)
        return result
    if number == 198:
        x, y = 0, 0
        for v in a:
            x, y = y, max(y, x + v)
        return y
    if number == 279:
        if isqrt(a) ** 2 == a:
            return 1
        for i in range(1, isqrt(a) + 1):
            if isqrt(a - i * i) ** 2 == a - i * i:
                return 2
        n = a
        while n % 4 == 0:
            n //= 4
        return 4 if n % 8 == 7 else 3
    if number == 322:
        amount, dp = args[1], [0] + [args[1] + 1] * args[1]
        for coin in a:
            for i in range(coin, amount + 1):
                dp[i] = min(dp[i], dp[i - coin] + 1)
        return -1 if dp[amount] > amount else dp[amount]
    if number == 139:
        words, lengths, dp = set(args[1]), set(map(len, args[1])), [True] + [False] * len(a)
        for i in range(1, len(a) + 1):
            dp[i] = any(i >= size and dp[i - size] and a[i - size:i] in words for size in lengths)
        return dp[-1]
    if number == 300:
        tails = []
        for x in a:
            i = bisect_left(tails, x)
            if i == len(tails):
                tails.append(x)
            else:
                tails[i] = x
        return len(tails)
    if number == 152:
        lo = hi = best = a[0]
        for x in a[1:]:
            lo, hi = min(x, x * lo, x * hi), max(x, x * lo, x * hi)
            best = max(best, hi)
        return best
    if number == 416:
        total, bits = sum(a), 1
        if total % 2:
            return False
        for x in a:
            bits |= bits << x
        return bool(bits >> (total // 2) & 1)
    if number == 32:
        stack, best = [-1], 0
        for i, c in enumerate(a):
            if c == '(':
                stack.append(i)
            else:
                stack.pop()
                if stack:
                    best = max(best, i - stack[-1])
                else:
                    stack.append(i)
        return best
    if number == 62:
        return comb(a + args[1] - 2, a - 1)
    if number == 64:
        dp = [float('inf')] * len(a[0]); dp[0] = 0
        for row in a:
            for j, x in enumerate(row):
                dp[j] = x + min(dp[j], dp[j - 1] if j else float('inf'))
        return dp[-1]
    if number == 5:
        best = ''
        for center in range(len(a)):
            for l, r in ((center, center), (center, center + 1)):
                while l >= 0 and r < len(a) and a[l] == a[r]:
                    if r - l + 1 > len(best):
                        best = a[l:r + 1]
                    l -= 1; r += 1
        return best
    if number == 1143:
        dp = [0] * (len(args[1]) + 1)
        for x in a:
            previous = 0
            for j, y in enumerate(args[1], 1):
                old = dp[j]; dp[j] = previous + 1 if x == y else max(dp[j], dp[j - 1]); previous = old
        return dp[-1]
    if number == 72:
        dp = list(range(len(args[1]) + 1))
        for i, x in enumerate(a, 1):
            previous, dp[0] = dp[0], i
            for j, y in enumerate(args[1], 1):
                old = dp[j]; dp[j] = previous if x == y else 1 + min(previous, dp[j], dp[j - 1]); previous = old
        return dp[-1]
    if number == 136:
        result = 0
        for x in a:
            result ^= x
        return result
    if number == 169:
        count, candidate = 0, None
        for x in a:
            if not count:
                candidate = x
            count += 1 if x == candidate else -1
        return candidate
    if number == 75:
        counts = Counter(a)
        return [x for x in range(3) for _ in range(counts[x])]
    if number == 31:
        result, i = a[:], len(a) - 2
        while i >= 0 and result[i] >= result[i + 1]:
            i -= 1
        if i >= 0:
            j = len(a) - 1
            while result[j] <= result[i]:
                j -= 1
            result[i], result[j] = result[j], result[i]
        result[i + 1:] = reversed(result[i + 1:])
        return result
    if number == 287:
        slow, fast = a[0], a[a[0]]
        while slow != fast:
            slow, fast = a[slow], a[a[fast]]
        fast = 0
        while slow != fast:
            slow, fast = a[slow], a[fast]
        return slow
    raise KeyError(f'没有参考计算：{number}')
