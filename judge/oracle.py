"""Independent small-input oracles used only by quality checks.

These deliberately use enumeration, simple models or different recurrences.
They do not import the production reference or its tree/codec helpers.
"""
from collections import deque
from functools import lru_cache
from itertools import combinations, permutations, product
from math import comb, prod
import re


def graph(values):
    if not values or values[0] is None:
        return [], []
    nodes, edges, queue, i = [values[0]], [[]], deque([0]), 1
    while queue and i<len(values):
        parent=queue.popleft()
        for _ in range(2):
            if i==len(values):
                edges[parent].append(None);continue
            value=values[i];i+=1
            if value is None:edges[parent].append(None)
            else:
                child=len(nodes);nodes.append(value);edges.append([]);edges[parent].append(child);queue.append(child)
    for children in edges:
        children.extend([None]*(2-len(children)))
    return nodes,edges


def pack_nested(node):
    if node is None:return []
    values=[];queue=deque([node])
    while queue:
        current=queue.popleft()
        values.append(current[0] if current else None)
        if current:queue.extend(current[1:])
    while values and values[-1] is None:values.pop()
    return values


def oracle(number,args):
    a=args[0]
    if number==1:
        return next([i,j] for i in range(len(a)) for j in range(i+1,len(a)) if a[i]+a[j]==args[1])
    if number==49:
        remaining=list(a);groups=[]
        while remaining:
            first=remaining.pop(0);group=[first]
            for i in range(len(remaining)-1,-1,-1):
                if sorted(remaining[i])==sorted(first):group.append(remaining.pop(i))
            groups.append(group)
        return groups
    if number==128:
        best=0
        for x in a:
            length=1
            while x+length in a:length+=1
            best=max(best,length)
        return best
    if number==283:return [x for x in a if x!=0]+[0 for x in a if x==0]
    if number==11:return max(min(a[i],a[j])*(j-i) for i in range(len(a)) for j in range(i+1,len(a)))
    if number==15:return [list(row) for row in sorted({tuple(sorted(row)) for row in combinations(a,3) if sum(row)==0})]
    if number==42:return sum(max(0,min(max(a[:i+1]),max(a[i:]))-a[i]) for i in range(len(a)))
    if number==3:return max([0]+[j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if len(set(a[i:j]))==j-i])
    if number==438:return [i for i in range(len(a)-len(args[1])+1) if sorted(a[i:i+len(args[1])])==sorted(args[1])]
    if number==560:return sum(sum(a[i:j])==args[1] for i in range(len(a)) for j in range(i+1,len(a)+1))
    if number==239:return [max(a[i:i+args[1]]) for i in range(len(a)-args[1]+1)]
    if number==76:
        candidates=[a[i:j] for i in range(len(a)) for j in range(i+1,len(a)+1) if all(a[i:j].count(c)>=args[1].count(c) for c in set(args[1]))]
        return min(candidates,key=len) if candidates else ''
    if number==53:return max(sum(a[i:j]) for i in range(len(a)) for j in range(i+1,len(a)+1))
    if number==56:
        # Merge connected components in the interval-overlap graph.
        remaining=set(range(len(a)));answer=[]
        while remaining:
            root=remaining.pop();component={root};queue=[root]
            while queue:
                i=queue.pop()
                for j in list(remaining):
                    if max(a[i][0],a[j][0])<=min(a[i][1],a[j][1]):remaining.remove(j);component.add(j);queue.append(j)
            answer.append([min(a[i][0] for i in component),max(a[i][1] for i in component)])
        return sorted(answer)
    if number==189:
        result=[0]*len(a)
        for i,x in enumerate(a):result[(i+args[1])%len(a)]=x
        return result
    if number==238:return [prod(a[:i]+a[i+1:]) for i in range(len(a))]
    if number==41:return next(i for i in range(1,len(a)+2) if i not in a)
    if number==73:return [[0 if 0 in a[i] or any(row[j]==0 for row in a) else a[i][j] for j in range(len(a[0]))] for i in range(len(a))]
    if number==54:
        x=y=direction=0;seen=set();result=[];m,n=len(a),len(a[0]);moves=[(0,1),(1,0),(0,-1),(-1,0)]
        for _ in range(m*n):
            result.append(a[x][y]);seen.add((x,y));dx,dy=moves[direction]
            if not (0<=x+dx<m and 0<=y+dy<n) or (x+dx,y+dy) in seen:direction=(direction+1)%4;dx,dy=moves[direction]
            x+=dx;y+=dy
        return result
    if number==48:return [[a[len(a)-1-j][i] for j in range(len(a))] for i in range(len(a))]
    if number in (74,240):return any(args[1] in row for row in a)
    if number==160:
        class Link:
            def __init__(self,v,nxt=None):self.v,self.next=v,nxt
        links=[];head=None
        for v in reversed(a):head=Link(v,head);links.append(head)
        links.reverse()
        head_b=links[args[2]] if args[2]>=0 else None
        for v in reversed(args[1][:args[3]] if args[3]>=0 else args[1]):head_b=Link(v,head_b)
        while head_b:
            for i,node in enumerate(links):
                if node is head_b:return i
            head_b=head_b.next
        return -1
    if number==206:
        answer=[]
        for value in a:answer.insert(0,value)
        return answer
    if number==234:return all(a[i]==a[len(a)-1-i] for i in range(len(a)//2))
    if number in (141,142):
        links=[{'next':None} for _ in a]
        for i in range(len(links)-1):links[i]['next']=links[i+1]
        if links and args[1]>=0:links[-1]['next']=links[args[1]]
        node=links[0] if links else None;seen={}
        while node is not None:
            if id(node) in seen:return True if number==141 else seen[id(node)]
            seen[id(node)]=len(seen);node=node['next']
        return False if number==141 else -1
    if number in (21,23):
        rows=[list(a),list(args[1])] if number==21 else [list(row) for row in a];result=[]
        while any(rows):
            index=min((i for i,row in enumerate(rows) if row),key=lambda i:rows[i][0]);result.append(rows[index].pop(0))
        return result
    if number==2:
        value=sum(x*10**i for i,x in enumerate(a))+sum(x*10**i for i,x in enumerate(args[1]))
        return list(map(int,str(value)[::-1]))
    if number==19:return [x for i,x in enumerate(a) if i!=len(a)-args[1]]
    if number in (24,25):
        result=[];k=2 if number==24 else args[1]
        for i in range(0,len(a),k):
            segment=a[i:i+k];result.extend([segment[len(segment)-1-j] for j in range(len(segment))] if len(segment)==k else segment)
        return result
    if number==138:
        original=[{'v':x} for x in a];clones=[{'v':node['v']} for node in original]
        for i,target in enumerate(args[1]):clones[i]['random']=clones[target] if target>=0 else None
        return [[node['v'] for node in clones],[next((j for j,x in enumerate(clones) if node['random'] is x),-1) for node in clones]]
    if number==148:
        values=a[:]
        for i in range(len(values)):
            for j in range(i+1,len(values)):
                if values[j]<values[i]:values[j],values[i]=values[i],values[j]
        return values
    if number==146:
        entries=[];result=[]
        for op in args[1]:
            index=next((i for i,p in enumerate(entries) if p[0]==op[1]),None)
            if op[0]=='get':
                result.append(entries[index][1] if index is not None else -1)
                if index is not None:entries.append(entries.pop(index))
            else:
                if index is not None:entries.pop(index)
                entries.append([op[1],op[2]])
                if len(entries)>a:entries.pop(0)
        return result
    if number in (94,104,226,101,543,102,108,98,230,199,114,105,437,236,124):
        if number==108:
            def build(values):
                if not values:return None
                i=(len(values)-1)//2;return [values[i],build(values[:i]),build(values[i+1:])]
            return pack_nested(build(a))
        if number==105:
            def build(pre,ino):
                if not pre:return None
                mid=ino.index(pre[0]);return [pre[0],build(pre[1:mid+1],ino[:mid]),build(pre[mid+1:],ino[mid+1:])]
            return pack_nested(build(a,args[1]))
        nodes,edges=graph(a)
        def traversal(index,order):
            if index is None:return []
            l,r=edges[index]
            return ([nodes[index]]+traversal(l,order)+traversal(r,order)) if order=='pre' else traversal(l,order)+[nodes[index]]+traversal(r,order)
        if number in (94,114):return traversal(0 if nodes else None,'in' if number==94 else 'pre')
        if number==226:
            def flip(index):
                if index is None:return None
                l,r=edges[index];return [nodes[index],flip(r),flip(l)]
            return pack_nested(flip(0 if nodes else None))
        if number==101:
            def equal(x,y):
                if x is None or y is None:return x==y
                return nodes[x]==nodes[y] and equal(edges[x][0],edges[y][1]) and equal(edges[x][1],edges[y][0])
            return not nodes or equal(*edges[0])
        if number in (104,102,199):
            by_depth={};queue=deque([(0,0)] if nodes else [])
            while queue:
                i,depth=queue.popleft();by_depth.setdefault(depth,[]).append(nodes[i])
                queue.extend((child,depth+1) for child in edges[i] if child is not None)
            levels=[by_depth[k] for k in sorted(by_depth)]
            return len(levels) if number==104 else levels if number==102 else [row[-1] for row in levels]
        if number==98:
            def good(i,lower,upper):
                if i is None:return True
                l,r=edges[i];return lower<nodes[i]<upper and good(l,lower,nodes[i]) and good(r,nodes[i],upper)
            return good(0,-float('inf'),float('inf'))
        if number==230:return sorted(nodes)[args[1]-1]
        if number==437:
            count=0
            for start in range(len(nodes)):
                stack=[(start,0)]
                while stack:
                    i,value=stack.pop();value+=nodes[i];count+=value==args[1]
                    stack.extend((child,value) for child in edges[i] if child is not None)
            return count
        parents={0:None} if nodes else {};adj=[[] for _ in nodes]
        for i,children in enumerate(edges):
            for child in children:
                if child is not None:parents[child]=i;adj[i].append(child);adj[child].append(i)
        if number==236:
            x=nodes.index(args[1]);y=nodes.index(args[2]);path=[]
            while x is not None:path.append(x);x=parents[x]
            while y not in path:y=parents[y]
            return nodes[y]
        best=0 if number==543 else -float('inf')
        for start in range(len(nodes)):
            stack=[(start,None,0,0)]
            while stack:
                i,parent,distance,total=stack.pop();total+=nodes[i]
                best=max(best,distance if number==543 else total)
                stack.extend((child,i,distance+1,total) for child in adj[i] if child!=parent)
        return best
    if number==200:
        # Disjoint-set components, independent of reference flood fill.
        m,n=len(a),len(a[0]);parent={i*n+j:i*n+j for i in range(m) for j in range(n) if a[i][j]=='1'}
        def find(i):
            while parent[i]!=i:i=parent[i]
            return i
        for i in range(m):
            for j in range(n):
                key=i*n+j
                if key not in parent:continue
                for x,y in ((i+1,j),(i,j+1)):
                    other=x*n+y
                    if x<m and y<n and other in parent:parent[find(key)]=find(other)
        return len({find(i) for i in parent})
    if number==994:
        grid=[row[:] for row in a];minutes=0
        while any(1 in row for row in grid):
            changed=[]
            for i,row in enumerate(grid):
                for j,value in enumerate(row):
                    if value==1 and any(0<=x<len(a) and 0<=y<len(a[0]) and grid[x][y]==2 for x,y in ((i-1,j),(i+1,j),(i,j-1),(i,j+1))):changed.append((i,j))
            if not changed:return -1
            for i,j in changed:grid[i][j]=2
            minutes+=1
        return minutes
    if number==207:
        adj=[[] for _ in range(a)]
        for x,y in args[1]:adj[x].append(y)
        visited=[0]*a
        def visit(i):
            if visited[i]==1:return False
            if visited[i]==2:return True
            visited[i]=1
            if any(not visit(j) for j in adj[i]):return False
            visited[i]=2;return True
        return all(visit(i) for i in range(a))
    if number==208:
        words=set();result=[]
        for op,s in a:
            if op=='insert':words.add(s)
            elif op=='search':result.append(s in words)
            else:result.append(any(w.startswith(s) for w in words))
        return result
    if number==46:
        def permute(values):
            if not values:return [[]]
            return [[x]+tail for i,x in enumerate(values) for tail in permute(values[:i]+values[i+1:])]
        return permute(a)
    if number==78:return [[a[i] for i in range(len(a)) if mask>>i&1] for mask in range(1<<len(a))]
    if number==17:
        result=[''];alphabet=['abc','def','ghi','jkl','mno','pqrs','tuv','wxyz']
        for digit in a:
            result=[s+c for s,c in product(result,alphabet[int(digit)-2])]
        return result
    if number==39:
        result=[]
        for counts in product(*(range(args[1]//x+1) for x in a)):
            if sum(x*c for x,c in zip(a,counts))==args[1]:result.append([x for x,c in zip(a,counts) for _ in range(c)])
        return result
    if number==22:
        result=[]
        for positions in combinations(range(2*a),a):
            positions=set(positions);s=''.join('(' if i in positions else ')' for i in range(2*a));level=0;valid=True
            for c in s:
                level+=1 if c=='(' else -1
                if level<0:valid=False;break
            if valid:result.append(s)
        return result
    if number==79:
        m,n=len(a),len(a[0]);word=args[1];queue=deque(([(i,j)],a[i][j]) for i in range(m) for j in range(n) if a[i][j]==word[0])
        while queue:
            path,s=queue.popleft()
            if s==word:return True
            i,j=path[-1]
            for x,y in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
                if 0<=x<m and 0<=y<n and (x,y) not in path and a[x][y]==word[len(s)]:queue.append((path+[(x,y)],s+a[x][y]))
        return False
    if number==131:
        result=[]
        for mask in range(1<<(len(a)-1)):
            row=[];start=0
            for i in range(len(a)-1):
                if mask>>i&1:row.append(a[start:i+1]);start=i+1
            row.append(a[start:])
            if all(s==s[::-1] for s in row):result.append(row)
        return result
    if number==51:
        result=[]
        for cols in permutations(range(a)):
            if len({i-col for i,col in enumerate(cols)})==a and len({i+col for i,col in enumerate(cols)})==a:result.append([''.join('Q' if j==col else '.' for j in range(a)) for col in cols])
        return result
    if number==35:return sum(x<args[1] for x in a)
    if number==34:
        positions=[i for i,x in enumerate(a) if x==args[1]]
        return [positions[0],positions[-1]] if positions else [-1,-1]
    if number==33:return next((i for i,x in enumerate(a) if x==args[1]),-1)
    if number==153:return min(a)
    if number==4:
        values=sorted(a+args[1]);return (values[(len(values)-1)//2]+values[len(values)//2])/2
    if number==20:
        while True:
            new=a.replace('()','').replace('[]','').replace('{}','')
            if a==new:return not a
            a=new
    if number==155:
        stack=[];result=[]
        for op in a:
            if op[0]=='push':stack.append(op[1])
            elif op[0]=='pop':stack.pop()
            else:result.append(stack[-1] if op[0]=='top' else min(stack))
        return result
    if number==394:
        while '[' in a:a=re.sub(r'(\d+)\[([a-z]*)\]',lambda match:int(match[1])*match[2],a)
        return a
    if number==739:
        return [next((j-i for j in range(i+1,len(a)) if a[j]>x),0) for i,x in enumerate(a)]
    if number==84:return max(min(a[i:j])*(j-i) for i in range(len(a)) for j in range(i+1,len(a)+1))
    if number==215:
        values=a[:]
        for _ in range(args[1]-1):values.remove(max(values))
        return max(values)
    if number==347:return sorted(set(a),key=lambda x:-a.count(x))[:args[1]]
    if number==295:
        values=[];result=[]
        for op in a:
            if op[0]=='addNum':values.append(op[1])
            else:
                ordered=sorted(values);result.append((ordered[(len(ordered)-1)//2]+ordered[len(ordered)//2])/2)
        return result
    if number==121:return max([0]+[a[j]-a[i] for i in range(len(a)) for j in range(i+1,len(a))])
    if number in (55,45):
        queue=deque([(0,0)]);seen={0}
        while queue:
            i,distance=queue.popleft()
            if i==len(a)-1:return True if number==55 else distance
            for j in range(i+1,min(len(a),i+a[i]+1)):
                if j not in seen:seen.add(j);queue.append((j,distance+1))
        return False if number==55 else -1
    if number==763:
        result=[];left=0
        while left<len(a):
            for right in range(left+1,len(a)+1):
                if not set(a[left:right])&set(a[right:]):result.append(right-left);left=right;break
        return result
    if number==70:
        @lru_cache(None)
        def count(n):return 1 if n<=1 else count(n-1)+count(n-2)
        return count(a)
    if number==118:return [[comb(i,j) for j in range(i+1)] for i in range(a)]
    if number==198:
        return max(sum(a[i] for i in range(len(a)) if mask>>i&1) for mask in range(1<<len(a)) if not mask&(mask<<1))
    if number==279:
        queue=deque([(0,0)]);seen={0}
        while queue:
            value,steps=queue.popleft()
            if value==a:return steps
            i=1
            while value+i*i<=a:
                new=value+i*i
                if new not in seen:seen.add(new);queue.append((new,steps+1))
                i+=1
    if number==322:
        reached={0};frontier={0};depth=0
        while frontier:
            if args[1] in frontier:return depth
            frontier={v+c for v in frontier for c in a if v+c<=args[1]}-reached;reached|=frontier;depth+=1
        return -1
    if number==139:
        reached={0}
        for i in range(len(a)):
            if i in reached:
                for word in args[1]:
                    if a.startswith(word,i):reached.add(i+len(word))
        return len(a) in reached
    if number==300:
        best=0
        for mask in range(1<<len(a)):
            row=[a[i] for i in range(len(a)) if mask>>i&1]
            if all(row[i]<row[i+1] for i in range(len(row)-1)):best=max(best,len(row))
        return best
    if number==152:return max(prod(a[i:j]) for i in range(len(a)) for j in range(i+1,len(a)+1))
    if number==416:return sum(a)%2==0 and any(sum(a[i] for i in range(len(a)) if mask>>i&1)==sum(a)//2 for mask in range(1<<len(a)))
    if number==32:
        best=0
        for i in range(len(a)):
            level=0
            for j in range(i,len(a)):
                level+=1 if a[j]=='(' else -1
                if level<0:break
                if level==0:best=max(best,j-i+1)
        return best
    if number==62:
        @lru_cache(None)
        def paths(m,n):return 1 if m==1 or n==1 else paths(m-1,n)+paths(m,n-1)
        return paths(*args)
    if number==64:
        @lru_cache(None)
        def minimum(i,j):
            if i==0 and j==0:return a[0][0]
            return a[i][j]+min(minimum(i-1,j) if i else float('inf'),minimum(i,j-1) if j else float('inf'))
        return minimum(len(a)-1,len(a[0])-1)
    if number==5:return max((a[i:j] for i in range(len(a)) for j in range(i+1,len(a)+1) if a[i:j]==a[i:j][::-1]),key=len)
    if number==1143:
        best=0
        for mask in range(1<<len(a)):
            row=''.join(a[i] for i in range(len(a)) if mask>>i&1);index=0
            for c in args[1]:
                if index<len(row) and c==row[index]:index+=1
            if index==len(row):best=max(best,len(row))
        return best
    if number==72:
        @lru_cache(None)
        def distance(i,j):
            if i==len(a):return len(args[1])-j
            if j==len(args[1]):return len(a)-i
            return distance(i+1,j+1) if a[i]==args[1][j] else 1+min(distance(i+1,j),distance(i,j+1),distance(i+1,j+1))
        return distance(0,0)
    if number==136:return next(x for x in a if a.count(x)==1)
    if number==169:return next(x for x in a if a.count(x)>len(a)//2)
    if number==75:return sorted(a)
    if number==31:
        values=sorted(set(permutations(a)));current=values.index(tuple(a));return list(values[(current+1)%len(values)])
    if number==287:return next(x for x in a if a.count(x)>1)
    raise KeyError(f'No independent oracle for {number}')
