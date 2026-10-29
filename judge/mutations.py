"""Named, deliberately wrong algorithm/output models for suite auditing.

These are quality fixtures, never used to compute a student's expected result.
Some models transform a correct answer to isolate a checker's obligation.
"""
from collections import Counter,deque
from itertools import combinations
from math import ceil,isqrt

from .reference import solve,tree,serialize,traversals

LABELS = {
1:'输出值而非下标',49:'用字符集合分组忽略重数',128:'不同元素个数当连续长度',283:'排序非零元素破坏稳定性',11:'只检查相邻容器',15:'不去重三元组',42:'只用全局最高墙',3:'统计全串不同字符',438:'忽略字符重数',560:'只统计从开头的子数组',239:'使用前缀最大值',76:'忽略目标字符重数',53:'只考虑单个元素',56:'漏合并接触端点',189:'向左轮转',238:'遇到零全部输出零',41:'返回最大值加一',73:'只修改原本为零的位置',54:'按行展开',48:'仅转置不旋转',240:'误当整行拼接有序',160:'将相同值当相交节点',206:'没有反转',234:'只比较首尾',141:'将重复值当作环',142:'输出入环节点值而非下标',21:'合并时丢弃重复值',2:'忽略进位',19:'从头删除第 n 个节点',24:'反转整条链表',25:'错误翻转末尾不足 k 个节点',138:'丢失 random 指向',148:'按绝对值排序',23:'去重合并结果',146:'使用 FIFO 而非 LRU',94:'前序代替中序',104:'把边数当节点深度',226:'直接反转层序数组',101:'把层序回文当树对称',543:'只考虑经过根的直径',102:'每个节点当一层',108:'构造不平衡 BST',98:'只比较直接父子',230:'k 下标偏移',199:'输出左视图',114:'中序代替展开前序',105:'重建时交换左右树',437:'只统计从根开始路径',236:'将普通树当 BST',124:'全负路径错误返回零',200:'错误允许对角相连',994:'无新鲜橘子时返回 -1',207:'共享依赖误判为环',208:'将前缀存在当完整单词存在',46:'只生成循环位移',78:'漏掉空子集',17:'遗漏 7/9 的第四字母',39:'将可重复选择当 0/1 选择',22:'只返回一种括号序列',79:'重复使用格子',131:'只按单字符切分',51:'遗漏对角线约束',35:'使用右插入位置',74:'只检查第一行',34:'仅返回第一个位置',33:'对旋转数组普通二分',153:'返回首元素',4:'偶数长度只取上中位数',20:'只数括号数量不检查顺序',155:'把栈顶当最小值',394:'忽略多位重复次数',739:'把相等温度当更高',84:'只考虑单柱面积',215:'去重后找第 k 大',347:'输出前 k 个输入值',295:'中位数取整',121:'忽略买卖先后顺序',55:'用总跳跃长度判断可达',45:'按全局最大跳跃估算步数',763:'每个字符单独分段',70:'斐波那契下标偏移',118:'三角形内部全为一',198:'只比较奇偶位置和',279:'贪心取最大平方',322:'贪心取最大硬币',139:'字符可用误当可以分词',300:'最长连续递增代替子序列',152:'忽略负负得正',416:'降序贪心凑一半',32:'只数左右括号对',62:'路径数量当格子数',64:'每步贪心走较小格子',5:'只检查奇数长度回文',1143:'最长公共子串代替子序列',72:'只统计对应字符差异',136:'返回首元素',169:'返回频数而非元素值',75:'颜色倒序排列',31:'总是排序到最小排列',287:'返回最后一个元素',
}


def faulty(n,args):
    a=args[0];answer=solve(n,args)
    if n==1:return [a[i] for i in answer]
    if n==49:
        groups={}
        for s in a:groups.setdefault(tuple(sorted(set(s))),[]).append(s)
        return list(groups.values())
    if n==128:return len(set(a))
    if n==283:return sorted(x for x in a if x)+[0]*a.count(0)
    if n==11:return max(min(a[i],a[i+1]) for i in range(len(a)-1))
    if n==15:return [list(sorted(row)) for row in combinations(a,3) if sum(row)==0]
    if n==42:return sum(max(a)-x for x in a)
    if n==3:return len(set(a))
    if n==438:return [i for i in range(len(a)-len(args[1])+1) if set(a[i:i+len(args[1])])==set(args[1])]
    if n==560:return sum(sum(a[:i])==args[1] for i in range(1,len(a)+1))
    if n==239:return [max(a[:i+args[1]]) for i in range(len(a)-args[1]+1)]
    if n==76:return solve(n,[a,''.join(sorted(set(args[1])))])
    if n==53:return max(a)
    if n==56:
        result=[]
        for l,r in sorted(a):
            if result and l<result[-1][1]:result[-1][1]=max(result[-1][1],r)
            else:result.append([l,r])
        return result
    if n==189:
        k=args[1]%len(a);return a[k:]+a[:k]
    if n==238:return [0]*len(a) if 0 in a else answer
    if n==41:return max(a)+1
    if n==73:return a
    if n==54:return [x for row in a for x in row]
    if n==48:return [list(row) for row in zip(*a)]
    if n==240:
        from bisect import bisect_left
        values=[x for row in a for x in row];i=bisect_left(values,args[1]);return i<len(values) and values[i]==args[1]
    if n==160:return next((i for i,x in enumerate(a) if x in args[1]),-1)
    if n==206:return a
    if n==234:return a[0]==a[-1]
    if n==141:return len(set(a))<len(a)
    if n==142:return a[args[1]] if args[1]>=0 else -1
    if n in (21,23):return sorted(set(answer))
    if n==2:return [((a[i] if i<len(a) else 0)+(args[1][i] if i<len(args[1]) else 0))%10 for i in range(max(len(a),len(args[1])))]
    if n==19:return a[:args[1]-1]+a[args[1]:]
    if n==24:return a[::-1]
    if n==25:return [x for i in range(0,len(a),args[1]) for x in a[i:i+args[1]][::-1]]
    if n==138:return [a,[-1]*len(a)]
    if n==148:return sorted(a,key=abs)
    if n==146:
        values={};order=deque();result=[]
        for op in args[1]:
            if op[0]=='get':result.append(values.get(op[1],-1))
            else:
                if op[1] not in values:order.append(op[1])
                values[op[1]]=op[2]
                if len(values)>a:del values[order.popleft()]
        return result
    if n==94:return traversals(tree(a))[0]
    if n==104:return max(0,answer-1)
    if n==226:return a[::-1]
    if n==101:return a==a[::-1]
    if n==543:
        root=tree(a)
        def height(node):return 0 if not node else 1+max(height(node.left),height(node.right))
        return height(root.left)+height(root.right)
    if n==102:return [[x] for row in answer for x in row]
    if n==108:
        result=[]
        for x in a:result.extend([x,None])
        return result[:-1]
    if n==98:
        root=tree(a);queue=[root]
        while queue:
            node=queue.pop()
            if node.left:
                if node.left.value>=node.value:return False
                queue.append(node.left)
            if node.right:
                if node.right.value<=node.value:return False
                queue.append(node.right)
        return True
    if n==230:return traversals(tree(a))[1][min(len([x for x in a if x is not None])-1,args[1])]
    if n==199:return [row[0] for row in solve(102,args)]
    if n==114:return traversals(tree(a))[1]
    if n==105:return solve(226,[answer])
    if n==437:
        root=tree(a);result=0;stack=[(root,0)]
        while stack:
            node,total=stack.pop()
            if node:
                total+=node.value;result+=total==args[1];stack.extend([(node.left,total),(node.right,total)])
        return result
    if n==236:
        node=tree(a)
        while node:
            if max(args[1:])<node.value:node=node.left
            elif min(args[1:])>node.value:node=node.right
            else:return node.value
        return args[1]
    if n==124:return max(0,answer)
    if n==200:
        seen=set();result=0
        for i,row in enumerate(a):
            for j,c in enumerate(row):
                if c=='0' or (i,j) in seen:continue
                result+=1;stack=[(i,j)];seen.add((i,j))
                while stack:
                    x,y=stack.pop()
                    for dx,dy in product_offsets():
                        xx,yy=x+dx,y+dy
                        if 0<=xx<len(a) and 0<=yy<len(a[0]) and a[xx][yy]=='1' and (xx,yy) not in seen:seen.add((xx,yy));stack.append((xx,yy))
        return result
    if n==994:return -1 if not any(1 in row for row in a) else answer
    if n==207:
        visited=set();adj=[[] for _ in range(a)]
        for x,y in args[1]:adj[x].append(y)
        def visit(i):
            if i in visited:return False
            visited.add(i);return all(visit(j) for j in adj[i])
        return all(visit(i) for i in range(a))
    if n==208:
        values=set();result=[]
        for op,s in a:
            if op=='insert':values.add(s)
            else:result.append(any(w.startswith(s) for w in values))
        return result
    if n==46:return [a[i:]+a[:i] for i in range(len(a))]
    if n==78:return [row for row in answer if row]
    if n==17:return [s for s in answer if 's' not in s and 'z' not in s]
    if n==39:return [list(row) for k in range(len(a)+1) for row in combinations(a,k) if sum(row)==args[1]]
    if n==22:return ['('*a+')'*a]
    if n==79:
        word=args[1]
        def visit(i,j,index):
            if a[i][j]!=word[index]:return False
            if index==len(word)-1:return True
            return any(0<=x<len(a) and 0<=y<len(a[0]) and visit(x,y,index+1) for x,y in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)))
        return any(visit(i,j,0) for i in range(len(a)) for j in range(len(a[0])))
    if n==131:return [list(a)]
    if n==51:return [['.'*i+'Q'+'.'*(a-i-1) for i in range(a)]]
    if n==35:return sum(x<=args[1] for x in a)
    if n==74:return args[1] in a[0]
    if n==34:
        positions=[i for i,x in enumerate(a) if x==args[1]];return [positions[0]]*2 if positions else [-1,-1]
    if n==33:
        from bisect import bisect_left
        i=bisect_left(a,args[1]);return i if i<len(a) and a[i]==args[1] else -1
    if n==153:return a[0]
    if n==4:return sorted(a+args[1])[(len(a)+len(args[1]))//2]
    if n==20:return all(a.count(l)==a.count(r) for l,r in zip('([{',')]}'))
    if n==155:
        result=[];stack=[]
        for op in a:
            if op[0]=='push':stack.append(op[1])
            elif op[0]=='pop':stack.pop()
            else:result.append(stack[-1])
        return result
    if n==394:
        import re
        result=a
        while '[' in result:result=re.sub(r'(\d+)\[([a-z]*)\]',lambda m:int(m[1][-1])*m[2],result)
        return result
    if n==739:return [next((j-i for j in range(i+1,len(a)) if a[j]>=x),0) for i,x in enumerate(a)]
    if n==84:return max(a)
    if n==215:
        values=sorted(set(a),reverse=True);return values[min(args[1]-1,len(values)-1)]
    if n==347:return a[:args[1]]
    if n==295:return [int(x) for x in answer]
    if n==121:return max(a)-min(a)
    if n==55:return sum(a)>=len(a)-1
    if n==45:return ceil((len(a)-1)/max(a)) if max(a) else 0
    if n==763:return [1]*len(a)
    if n==70:return solve(70,[max(1,a-1)])
    if n==118:return [[1]*(i+1) for i in range(a)]
    if n==198:return max(sum(a[::2]),sum(a[1::2]))
    if n==279:
        count=0
        while a:a-=isqrt(a)**2;count+=1
        return count
    if n==322:
        remaining=args[1];count=0
        for coin in sorted(a,reverse=True):q,remaining=divmod(remaining,coin);count+=q
        return -1 if remaining else count
    if n==139:return set(a)<=set(''.join(args[1]))
    if n==300:
        longest=run=1
        for i in range(1,len(a)):run=run+1 if a[i]>a[i-1] else 1;longest=max(longest,run)
        return longest
    if n==152:return max(a)
    if n==416:
        if sum(a)%2:return False
        remaining=sum(a)//2
        for x in sorted(a,reverse=True):
            if x<=remaining:remaining-=x
        return remaining==0
    if n==32:return 2*min(a.count('('),a.count(')'))
    if n==62:return a*args[1]
    if n==64:
        i=j=0;result=a[0][0]
        while i<len(a)-1 or j<len(a[0])-1:
            if i==len(a)-1:j+=1
            elif j==len(a[0])-1:i+=1
            elif a[i+1][j]<a[i][j+1]:i+=1
            else:j+=1
            result+=a[i][j]
        return result
    if n==5:return max((a[i:j] for i in range(len(a)) for j in range(i+1,len(a)+1) if (j-i)%2 and a[i:j]==a[i:j][::-1]),key=len)
    if n==1143:return max([0]+[j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if a[i:j] in args[1]])
    if n==72:return abs(len(a)-len(args[1]))+sum(x!=y for x,y in zip(a,args[1]))
    if n==136:return a[0]
    if n==169:return max(Counter(a).values())
    if n==75:return sorted(a,reverse=True)
    if n==31:return sorted(a)
    if n==287:return a[-1]
    raise KeyError(n)


def product_offsets():
    return [(i,j) for i in (-1,0,1) for j in (-1,0,1) if i or j]
