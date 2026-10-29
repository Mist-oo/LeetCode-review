"""Check generated/custom inputs against each problem's published domain.

This is separate from the solution and from the parser: malformed or illegal
custom data must be rejected, not used to blame a student's correct program.
"""
from collections import Counter
from math import comb

from .protocols import ProtocolError, SPECS
from .reference import tree, traversals


def require(ok, message):
    if not ok:
        raise ProtocolError(message)


def numbers(values, minimum, maximum):
    return all(type(x) is int and minimum <= x <= maximum for x in values)


# Length min/max and numeric bounds for primary numeric array fields.
ARRAYS = {
    1:(2,10000,-10**9,10**9),128:(0,100000,-10**9,10**9),283:(1,10000,-2**31,2**31-1),
    11:(2,100000,0,10000),15:(3,3000,-100000,100000),42:(1,20000,0,100000),
    560:(1,20000,-1000,1000),239:(1,100000,-10000,10000),53:(1,100000,-10000,10000),
    189:(1,100000,-2**31,2**31-1),238:(2,100000,-30,30),41:(1,100000,-2**31,2**31-1),
    160:(1,30000,1,100000),206:(0,5000,-5000,5000),234:(1,100000,0,9),
    141:(0,10000,-100000,100000),142:(0,10000,-100000,100000),21:(0,50,-100,100),
    2:(1,100,0,9),19:(1,30,0,100),24:(0,100,0,100),25:(1,5000,0,1000),
    138:(0,1000,-10000,10000),148:(0,50000,-100000,100000),108:(1,10000,-10000,10000),
    46:(1,6,-10,10),78:(1,10,-10,10),39:(1,30,2,40),35:(1,10000,-10000,10000),
    34:(0,100000,-10**9,10**9),33:(1,5000,-10000,10000),153:(1,5000,-5000,5000),
    739:(1,100000,30,100),84:(1,100000,0,10000),215:(1,100000,-10000,10000),
    347:(1,100000,-10000,10000),121:(1,100000,0,10000),55:(1,10000,0,100000),
    45:(1,10000,0,1000),198:(1,100,0,400),322:(1,12,1,2**31-1),300:(1,2500,-10000,10000),
    152:(1,20000,-10,10),416:(1,200,1,100),136:(1,30000,-30000,30000),
    169:(1,50000,-10**9,10**9),75:(1,300,0,2),31:(1,100,0,100),287:(2,100001,1,100000),
}
TREES = {
    94:(0,100,-100,100),104:(0,10000,-100,100),226:(0,100,-100,100),101:(1,1000,-100,100),
    543:(1,10000,-100,100),102:(0,2000,-1000,1000),98:(1,10000,-2**31,2**31-1),
    230:(1,10000,0,10000),199:(0,100,-100,100),114:(0,2000,-100,100),
    437:(0,1000,-10**9,10**9),236:(2,100000,-10**9,10**9),124:(1,30000,-1000,1000),
}
STRINGS = {3:(0,100000),5:(1,1000),17:(1,4),20:(1,10000),32:(0,30000),
           76:(1,100000),438:(1,30000),79:(1,15),131:(1,16),139:(1,300),
           394:(1,30),763:(1,500),1143:(1,1000),72:(0,500)}


def validate(number, args):
    require(number in SPECS and len(args) == len(SPECS[number].fields), '题目或字段数量不正确')
    a = args[0]
    if number in ARRAYS:
        lo,hi,x,y=ARRAYS[number]
        require(lo<=len(a)<=hi and numbers(a,x,y), '数组长度或元素超出原题范围')
    if number in STRINGS:
        lo,hi=STRINGS[number]
        values = args if number in (76,438,1143,72) else [args[1] if number==79 else a]
        require(all(lo<=len(s)<=hi and '\n' not in s and '\r' not in s for s in values), '字符串长度超出原题范围')
        alphabet = ('23456789' if number==17 else '()[]{}' if number==20 else '()' if number==32 else None)
        if alphabet:
            require(all(c in alphabet for c in a), '字符串包含不允许的字符')
        if number in (438,131,139,763,1143,72):
            require(all(all('a'<=c<='z' for c in s) for s in values), '只允许小写英文字母')
        if number==76:
            require(all(all(c.isascii() and c.isalpha() for c in s) for s in values), '只允许大小写英文字母')
        if number==5:
            require(a.isascii() and a.isalnum(), '只允许英文字母和数字')
    if number==1:
        require(-10**9<=args[1]<=10**9,'target 超出范围')
        counts,total=Counter(),0
        for x in a:
            total+=counts[args[1]-x];counts[x]+=1
        require(total==1,'两数之和要求恰好存在一个有效下标对')
    if number==49:
        require(1<=len(a)<=10000 and all(len(s)<=100 and all('a'<=c<='z' for c in s) for s in a),'字母异位词输入超出范围')
    if number in (239,215):require(1<=args[1]<=len(a),'k 超出范围')
    if number==560:require(-10**7<=args[1]<=10**7,'k 超出范围')
    if number==189:require(0<=args[1]<=100000,'k 超出范围')
    if number==152:
        minimum=maximum=a[0]
        for x in a[1:]:
            minimum,maximum=min(x,x*minimum,x*maximum),max(x,x*minimum,x*maximum)
            require(-2**31<=minimum and maximum<=2**31-1,'子数组乘积超出原题 32 位范围')
    if number==238:
        zero=a.count(0)
        if zero<2:
            product=1
            for x in a:
                if x:product*=x
                require(abs(product)<=2**31*30,'输出乘积超出 32 位范围')
            require(all(-2**31<=(0 if zero and x else product//x if x else product)<=2**31-1 for x in a),'输出乘积超出 32 位范围')
    if number==56:require(1<=len(a)<=10000 and all(len(row)==2 and 0<=row[0]<=row[1]<=10000 for row in a),'区间超出范围')
    if number in (73,54,48,240,74,994,64,200,79):
        maxdim={73:200,54:10,48:20,240:300,74:100,994:10,64:200,200:300,79:6}[number]
        require(1<=len(a)<=maxdim and a and 1<=len(a[0])<=maxdim and all(len(row)==len(a[0]) for row in a),'矩阵尺寸超出原题范围')
        if number==48:require(len(a)==len(a[0]),'旋转图像要求方阵')
        if number in (200,79):
            require(all(c in '01' if number==200 else c.isascii() and c.isalpha() for row in a for c in row),'字符矩阵内容无效')
        else:
            lo,hi={73:(-2**31,2**31-1),54:(-100,100),48:(-1000,1000),240:(-10**9,10**9),74:(-10000,10000),994:(0,2),64:(0,200)}[number]
            require(all(numbers(row,lo,hi) for row in a),'矩阵元素超出范围')
        if number in (74,240):
            require(-10000<=args[1]<=10000 if number==74 else -10**9<=args[1]<=10**9,'target 超出范围')
            require(all(row==sorted(row) for row in a),'各行必须有序')
            if number==74:require(all(a[i][-1]<a[i+1][0] for i in range(len(a)-1)),'每行首元素应大于上一行末元素')
            else:require(all(a[i][j]<=a[i+1][j] for i in range(len(a)-1) for j in range(len(a[0]))),'各列必须有序')
    if number==160:
        b,sa,sb=args[1:]
        require(1<=len(b)<=30000 and numbers(b,1,100000),'listB 超出范围')
        require((sa==sb==-1) or (0<=sa<len(a) and 0<=sb<len(b) and a[sa:]==b[sb:]),'共享尾部描述不一致')
    if number in (141,142):require(args[1]==-1 or 0<=args[1]<len(a),'入环下标超出范围')
    if number in (21,2):
        b=args[1];lo,hi,x,y=ARRAYS[number]
        require(lo<=len(b)<=hi and numbers(b,x,y),'第二条链表超出范围')
        if number==21:require(a==sorted(a) and b==sorted(b),'链表必须非递减')
        else:require((len(a)==1 or a[-1]!=0) and (len(b)==1 or b[-1]!=0),'数字不得有前导零')
    if number in (19,25):require(1<=args[1]<=len(a),'n/k 超出链表长度')
    if number==138:require(len(args[1])==len(a) and numbers(args[1],-1,len(a)-1),'random 数组长度或下标无效')
    if number==23:require(len(a)<=10000 and sum(map(len,a))<=10000 and all(len(row)<=500 and row==sorted(row) and numbers(row,-10000,10000) for row in a),'链表集合超出范围或未排序')
    if number in TREES:
        root=tree(a);values=[x for x in a if x is not None];lo,hi,x,y=TREES[number]
        require(lo<=len(values)<=hi and numbers(values,x,y),'树节点数量或值超出范围')
        if number==230:
            ino=traversals(root)[1]
            require(all(ino[i]<ino[i+1] for i in range(len(ino)-1)) and 1<=args[1]<=len(values),'输入必须是 BST 且 k 有效')
        if number==236:require(len(values)==len(set(values)) and args[1]!=args[2] and args[1] in values and args[2] in values,'最近公共祖先节点要求不符合')
        if number==437:require(-1000<=args[1]<=1000,'targetSum 超出范围')
    if number==108:require(all(a[i]<a[i+1] for i in range(len(a)-1)),'数组必须严格递增')
    if number==105:
        b=args[1]
        require(1<=len(a)<=3000 and len(a)==len(b)==len(set(a)) and set(a)==set(b) and numbers(a,-3000,3000),'前序/中序节点无效')
        # Check consistency, not merely equality of the node sets.
        stack=[];i=0
        for x in a:
            stack.append(x)
            while stack and i<len(b) and stack[-1]==b[i]:stack.pop();i+=1
        require(not stack,'前序和中序不描述同一棵树')
    if number==207:require(1<=a<=2000 and len(args[1])<=5000 and len(set(map(tuple,args[1])))==len(args[1]) and all(len(row)==2 and numbers(row,0,a-1) for row in args[1]),'课程或依赖关系无效')
    if number in (46,78,39):require(len(a)==len(set(a)),'输入元素应互不相同')
    if number==39:require(1<=args[1]<=40,'target 超出范围')
    if number in (22,51):require(1<=a<=(8 if number==22 else 9),'n 超出范围')
    if number in (35,34):
        require(a==sorted(a),'数组必须非递减')
        if number==35:require(len(a)==len(set(a)),'数组应无重复元素')
        require((-10000<=args[1]<=10000) if number==35 else (-10**9<=args[1]<=10**9),'target 超出范围')
    if number in (33,153):
        require(len(a)==len(set(a)) and sum(a[i]>a[(i+1)%len(a)] for i in range(len(a)))<=1,'数组必须是严格递增数组的旋转')
        if number==33:require(-10000<=args[1]<=10000,'target 超出范围')
    if number==4:
        require(1<=len(a)+len(args[1])<=2000 and all(len(row)<=1000 and row==sorted(row) and numbers(row,-10**6,10**6) for row in args),'有序数组长度或数值无效')
    if number in (146,155,208,295):
        ops=args[1] if number==146 else a
        maximum={146:200000,155:30000,208:30000,295:50000}[number]
        require(1<=len(ops)<=maximum,'操作次数超出范围')
        if number==146:
            require(1<=a<=3000,'capacity 超出范围')
            for op in ops:
                require(0<=op[1]<=10000 and (op[0]!='put' or 0<=op[2]<=100000),'LRU 操作参数超出范围')
        elif number==208:
            require(all(1<=len(op[1])<=2000 and all('a'<=c<='z' for c in op[1]) for op in ops),'Trie 单词超出范围')
        else:
            count=0
            for op in ops:
                if op[0] in ('push','addNum'):
                    require(-2**31<=op[1]<=2**31-1 if number==155 else -100000<=op[1]<=100000,'操作值超出范围');count+=1
                else:
                    require(count>0,'不能在空数据结构上执行 pop 或查询')
                    count-=op[0]=='pop'
    if number==394:
        stack=[];index=0;length=0
        while index<len(a):
            c=a[index]
            if c.isdigit():
                end=index
                while end<len(a) and a[end].isdigit():end+=1
                count=int(a[index:end]);require(1<=count<=300 and end<len(a) and a[end]=='[','编码重复次数无效')
                stack.append((length,count));length=0;index=end+1;continue
            if c==']':
                require(bool(stack),'编码括号不匹配');old,count=stack.pop();length=old+count*length
            else:require('a'<=c<='z','编码包含无效字符');length+=1
            require(length<=100000,'解码输出超过原题上限');index+=1
        require(not stack,'编码括号不匹配')
    if number==347:
        counts=sorted(Counter(a).values(),reverse=True);k=args[1]
        require(1<=k<=len(counts) and (k==len(counts) or counts[k-1]>counts[k]),'前 k 高频集合应唯一')
    if number==45:
        reach=0
        for i,x in enumerate(a):
            require(i<=reach,'跳跃游戏 II 输入应能到达末尾');reach=max(reach,i+x)
    if number==70:require(1<=a<=45,'n 超出范围')
    if number==118:require(1<=a<=30,'numRows 超出范围')
    if number==279:require(1<=a<=10000,'n 超出范围')
    if number==322:require(0<=args[1]<=10000,'amount 超出范围')
    if number==139:require(1<=len(args[1])<=1000 and len(args[1])==len(set(args[1])) and all(1<=len(w)<=20 and all('a'<=c<='z' for c in w) for w in args[1]),'wordDict 不符合要求')
    if number==62:require(1<=a<=100 and 1<=args[1]<=100 and comb(a+args[1]-2,a-1)<=2*10**9,'尺寸或路径数量超出原题范围')
    if number==136:
        counts=Counter(a);require(list(counts.values()).count(1)==1 and all(c in (1,2) for c in counts.values()),'必须仅一个数出现一次，其余数各两次')
    if number==169:require(max(Counter(a).values())>len(a)//2,'必须存在严格多数元素')
    if number==287:
        counts=Counter(a);require(max(a)<=len(a)-1 and sum(v>1 for v in counts.values())==1,'只能有一个不同的重复值，元素在 1..n 范围')
    return True
