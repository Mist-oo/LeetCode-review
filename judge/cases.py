"""Deterministic legal cases plus seeded strengthening; no official hidden data.

SAMPLES and boundary cases are intentionally human-readable. Pressure fixtures
reach the published dimension limits; all generators are checked by validation.
"""
import random
from collections import Counter
from itertools import chain
from math import comb

from .reference import Node, serialize, traversals

EDGES = {
    1: [[[2,7,11,15],9], [[3,3],6], [[-10**9,10**9],0]],
    49: [[['eat','tea','tan','ate','nat','bat']], [['']], [['','', 'a','a']], [['a','aa','ab','aab']]],
    128: [[[100,4,200,1,3,2]], [[]], [[0,0,-1,1]]],
    283: [[[0,1,0,3,12]], [[0]], [[1]], [[0,0,0]]],
    11: [[[1,8,6,2,5,4,8,3,7]], [[0,0]], [[1,1]], [[2,3,4,5,18,17,6]]],
    15: [[[-1,0,1,2,-1,-4]], [[0,0,0,0]], [[1,2,3]], [[-100000,0,100000]]],
    42: [[[0,1,0,2,1,0,1,3,2,1,2,1]], [[0]], [[4,2,0,3,2,5]], [[3,0,3]]],
    3: [['abcabcbb'], [''], [' '], ['abba'], ['dvdf'], ['a b!a']],
    438: [['cbaebabacd','abc'], ['abab','ab'], ['a','aa'], ['aa','a']],
    560: [[[1,1,1],2], [[0,0,0],0], [[-1,-1,1],0], [[1],0]],
    239: [[[1,3,-1,-3,5,3,6,7],3], [[1],1], [[2,2,2],2], [[9,8,7],3]],
    76: [['ADOBECODEBANC','ABC'], ['a','aa'], ['aa','aa'], ['aA','A'], ['bba','ab']],
    53: [[[-2,1,-3,4,-1,2,1,-5,4]], [[-1]], [[-5,-2,-3]], [[0,0,0]]],
    56: [[[[1,3],[2,6],[8,10],[15,18]]], [[[1,4],[4,5]]], [[[0,0]]], [[[2,3],[1,9],[4,6]]]],
    189: [[[1,2,3,4,5,6,7],3], [[1],0], [[1,2,3],6], [[-2147483648,2147483647],1]],
    238: [[[1,2,3,4]], [[0,0]], [[0,-1,2]], [[-1,-1]]],
    41: [[[3,4,-1,1]], [[1,2,0]], [[1]], [[2]], [[2147483647,-2147483648]]],
    73: [[[[1,1,1],[1,0,1],[1,1,1]]], [[[0,1,2,0],[3,4,5,2],[1,3,1,5]]], [[[1]]], [[[0]]]],
    54: [[[[1,2,3],[4,5,6],[7,8,9]]], [[[1,2,3]]], [[[1],[2],[3]]], [[[5]]]],
    48: [[[[1,2],[3,4]]], [[[7]]], [[[1,2,3],[4,5,6],[7,8,9]]]],
    240: [[[[1,4,7],[2,5,8],[3,6,9]],6], [[[1]],0], [[[-3,-2],[-1,0]],-2]],
    160: [[[4,1,8,4,5],[5,6,1,8,4,5],2,3], [[1],[1],-1,-1], [[1],[1],0,0]],
    206: [[[1,2,3,4,5]], [[]], [[1]]],
    234: [[[1,2,2,1]], [[1]], [[1,2]], [[0,1,0]], [[1,2,3,1]]],
    141: [[[3,2,0,-4],1], [[], -1], [[1],0], [[1],-1]],
    142: [[[3,2,0,-4],1], [[], -1], [[1],0], [[1],-1]],
    21: [[[1,2,4],[1,3,4]], [[],[]], [[],[0]], [[-100,100],[-100,100]]],
    2: [[[2,4,3],[5,6,4]], [[0],[0]], [[9,9,9],[1]]],
    19: [[[1,2,3,4,5],2], [[1],1], [[1,2],2]],
    24: [[[1,2,3,4]], [[]], [[1]], [[1,2,3]]],
    25: [[[1,2,3,4,5],2], [[1,2,3],3], [[1],1]],
    138: [[[7,13,11,10,1],[-1,0,4,2,0]], [[],[]], [[1],[0]], [[1,1],[1,0]]],
    148: [[[4,2,1,3]], [[]], [[1]], [[-1,5,3,4,0]], [[2,2,1]]],
    23: [[[[1,4,5],[1,3,4],[2,6]]], [[]], [[[],[]]], [[[1]]]],
    146: [[2,[['put',1,1],['put',2,2],['get',1],['put',3,3],['get',2],['put',4,4],['get',1],['get',3],['get',4]]], [1,[['put',1,1],['put',1,2],['get',1],['put',2,3],['get',1],['get',2]]], [1,[['get',1]]]],
    94: [[[1,None,2,3]], [[]], [[-100]]],
    104: [[[3,9,20,None,None,15,7]], [[]], [[1]]],
    226: [[[4,2,7,1,3,6,9]], [[]], [[1,None,2]]],
    101: [[[1,2,2,3,4,4,3]], [[1,2,2,None,3,None,3]], [[1]]],
    543: [[[1,2,3,4,5]], [[1]], [[1,2,None,3,None,4]]],
    102: [[[3,9,20,None,None,15,7]], [[]], [[1,2,None,3]]],
    108: [[[-10,-3,0,5,9]], [[1]], [[1,2]]],
    98: [[[2,1,3]], [[5,1,4,None,None,3,6]], [[2,2,3]], [[2147483647]], [[5,3,8,None,6]]],
    230: [[[3,1,4,None,2],1], [[1],1], [[2,1,3],3]],
    199: [[[1,2,3,None,5,None,4]], [[]], [[1,2,None,3]]],
    114: [[[1,2,5,3,4,None,6]], [[]], [[1,None,2]]],
    105: [[[3,9,20,15,7],[9,3,15,20,7]], [[-1],[-1]], [[1,2,3],[3,2,1]]],
    437: [[[10,5,-3,3,2,None,11,3,-2,None,1],8], [[],0], [[0,0,0],0], [[-1,-1,-1],-2]],
    236: [[[3,5,1,6,2,0,8,None,None,7,4],5,1], [[1,2],1,2], [[3,1,4,None,2],1,2]],
    124: [[[-10,9,20,None,None,15,7]], [[-3]], [[-2,-1]], [[1,-2,3]]],
    200: [[[list('110'),list('010'),list('001')]], [[list('0')]], [[list('1')]], [[list('10'),list('01')]]],
    994: [[[[2,1,1],[1,1,0],[0,1,1]]], [[[2,1,1],[0,1,1],[1,0,1]]], [[[0]]], [[[1]]], [[[2]]]],
    207: [[2,[[1,0]]], [2,[[1,0],[0,1]]], [1,[]], [1,[[0,0]]]],
    208: [[[['insert','apple'],['search','apple'],['search','app'],['startsWith','app'],['insert','app'],['search','app']]], [[['search','a'],['insert','a'],['search','a']]], [[['insert','ab'],['insert','ab'],['search','a']]]],
    46: [[[1,2,3]], [[0]], [[-1,1]]],
    78: [[[1,2,3]], [[0]], [[-1,1]]],
    17: [['23'], ['2'], ['79']],
    39: [[[2,3,6,7],7], [[2],1], [[2,3,5],8], [[40],40]],
    22: [[3],[1],[2]],
    79: [[[list('ABCE'),list('SFCS'),list('ADEE')],'ABCCED'], [[list('A')],'A'], [[list('AA')],'AAA'], [[list('AB'),list('CD')],'ACDB']],
    131: [['aab'],['a'],['aaa'],['abcd']],
    51: [[4],[1],[2],[3]],
    35: [[[1,3,5,6],5], [[1,3],0], [[1,3],4], [[1],1]],
    74: [[[[1,3,5],[7,9,11]],9], [[[1]],2], [[[-3,-1],[2,4]],-3]],
    34: [[[5,7,7,8,8,10],8], [[],0], [[1,1,1],1], [[1,2],3]],
    33: [[[4,5,6,7,0,1,2],0], [[1],0], [[1,3],3], [[3,1],1]],
    153: [[[3,4,5,1,2]], [[1]], [[1,2,3]], [[2,1]]],
    4: [[[1,3],[2]], [[],[1]], [[-1],[1]], [[1,2],[3,4]]],
    20: [['()[]{}'],['([)]'],[']'],['((()))'],['((']],
    155: [[[['push',-2],['push',0],['push',-3],['getMin'],['pop'],['top'],['getMin']]], [[['push',-2147483648],['push',2147483647],['getMin'],['pop'],['top']]]],
    394: [['3[a2[c]]'],['abc'],['10[a]'],['2[abc]3[cd]ef']],
    739: [[[73,74,75,71,69,72,76,73]], [[30]], [[30,30,31]], [[100,99,98]]],
    84: [[[2,1,5,6,2,3]], [[0]], [[2,2]], [[1,2,3,4]]],
    215: [[[3,2,1,5,6,4],2], [[1],1], [[2,2,1],2]],
    347: [[[1,1,1,2,2,3],2], [[1],1], [[-1,-1,0,0,0],1]],
    295: [[[['addNum',1],['addNum',2],['findMedian'],['addNum',3],['findMedian']]], [[['addNum',-100000],['findMedian'],['addNum',100000],['findMedian']]]],
    121: [[[7,1,5,3,6,4]], [[7,6,4,3,1]], [[0]], [[2,4,1]]],
    55: [[[2,3,1,1,4]], [[3,2,1,0,4]], [[0]], [[1,0,1]]],
    45: [[[2,3,1,1,4]], [[2,3,0,1,4]], [[0]], [[1,1,1,1]]],
    763: [['ababcbacadefegdehijhklij'],['a'],['aaaa'],['abc']],
    70: [[2],[1],[3],[45]],
    118: [[5],[1],[2],[30]],
    198: [[[1,2,3,1]], [[0]], [[2,1,1,2]], [[1,2]]],
    279: [[12],[13],[1],[7],[16]],
    322: [[[1,2,5],11], [[2],3], [[1],0], [[2147483647],10000]],
    139: [['leetcode',['leet','code']], ['catsandog',['cats','dog','sand','and','cat']], ['aaaaaaa',['aaa','aaaa']], ['a',['b']]],
    300: [[[10,9,2,5,3,7,101,18]], [[7,7,7]], [[1]], [[3,2,1]], [[0,1,0,3,2,3]]],
    152: [[[2,3,-2,4]], [[-2,0,-1]], [[-2]], [[-2,3,-4]], [[0,0]]],
    416: [[[1,5,11,5]], [[1,2,3,5]], [[1]], [[2,2]], [[1,2,5]], [[2,2,2,2,3,3]]],
    32: [[')()())'],[''],['(()'],['()(())'],[')))']],
    62: [[3,7],[1,1],[100,1],[1,100]],
    64: [[[[1,3,1],[1,5,1],[4,2,1]]], [[[0]]], [[[1,2,3]]], [[[1],[2],[3]]]],
    5: [['babad'],['cbbd'],['a'],['aaaa'],['ac']],
    1143: [['abcde','ace'],['abc','def'],['aaaa','aa'],['a','a']],
    72: [['horse','ros'],['',''],['','abc'],['ab','ba']],
    136: [[[4,1,2,1,2]], [[0]], [[-1,2,2]]],
    169: [[[2,2,1,1,1,2,2]], [[1]], [[-1,-1,0]]],
    75: [[[2,0,2,1,1,0]], [[0]], [[2,1,0]], [[1,1]]],
    31: [[[1,2,3]], [[3,2,1]], [[1,1,5]], [[1]], [[1,3,2]]],
    287: [[[1,3,4,2,2]], [[1,1]], [[3,3,3,3,3]], [[2,1,2]]],
}


def random_tree(rng, n, unique=False, bst=False):
    if not n:
        return []
    values = rng.sample(range(-100, 101), n) if unique or bst else [rng.randint(-3, 3) for _ in range(n)]
    root = Node(values[0])
    if bst:
        for value in values[1:]:
            node = root
            while True:
                side = 'left' if value < node.value else 'right'
                child = getattr(node, side)
                if child:
                    node = child
                else:
                    setattr(node, side, Node(value)); break
    else:
        available = [(root, 'left'), (root, 'right')]
        for value in values[1:]:
            i = rng.randrange(len(available)); parent, side = available.pop(i)
            node = Node(value); setattr(parent, side, node)
            available.extend([(node, 'left'), (node, 'right')])
    return serialize(root)


def random_case(number, rng):
    n = rng.randint(1, 8)
    ints = lambda minimum=1, maximum=8, low=-5, high=5: [rng.randint(low, high) for _ in range(rng.randint(minimum, maximum))]
    word = lambda minimum=1, maximum=8, alphabet='abc': ''.join(rng.choice(alphabet) for _ in range(rng.randint(minimum, maximum)))
    matrix = lambda maxdim=4, low=-3, high=3: [[rng.randint(low, high) for _ in range(rng.randint(1, maxdim))]]
    if number == 1:
        values = rng.sample(range(-50, 51), n + 1)
        pairs = [(i,j) for i in range(len(values)) for j in range(i+1,len(values))]
        rng.shuffle(pairs)
        for i,j in pairs:
            target=values[i]+values[j]
            if sum(values[x]+values[y]==target for x,y in pairs)==1:
                return [values,target]
        return [[1,3],4]
    if number == 49:
        return [[word(0,5) for _ in range(n)]]
    if number in (128,283,53,41,148,136,169,238,152,198,121,11,42,55,45,739,84,300,75,31,287,46,78,189,560,239,215,347,416):
        values=ints(0 if number in (128,148) else 2 if number in (238,11) else 1)
        if number in (11,42,55,45,121,198,84):
            values=[abs(x) for x in values]
        if number == 45:
            values=[max(1,x) for x in values]
        if number == 739:
            values=[rng.randint(30,100) for _ in values]
        if number == 75:
            values=[rng.randrange(3) for _ in values]
        if number == 31:
            values=[abs(x) for x in values]
        if number == 136:
            distinct=rng.sample(range(-10,11),n);values=list(chain.from_iterable([x,x] for x in distinct[:-1]))+[distinct[-1]];rng.shuffle(values)
        if number == 169:
            value=rng.randint(-5,5);values=[value]*(n//2+1)+ints(n-n//2-1,n-n//2-1);rng.shuffle(values)
        if number == 287:
            values=list(range(1,n+1))+[rng.randint(1,n)];rng.shuffle(values)
        if number in (46,78):
            values=rng.sample(range(-10,11),min(n,6 if number==46 else 8))
        if number == 416:
            values=[abs(x)+1 for x in values]
        if number == 189:
            return [values,rng.randint(0,30)]
        if number == 560:
            return [values,rng.randint(-8,8)]
        if number in (239,215):
            return [values,rng.randint(1,len(values))]
        if number == 347:
            # Unique top-k cutoff, as required by the original problem.
            distinct=rng.sample(range(-10,11),n);values=list(chain.from_iterable([x]*(i+1) for i,x in enumerate(distinct)));rng.shuffle(values)
            return [values,rng.randint(1,n)]
        return [values]
    if number == 15:
        return [ints(3,9)]
    if number in (3,5,20,32,17,22,51,131,394,763,70,118,279):
        if number==3:return [word(0,10,'ab A!9')]
        if number in (5,131,763):return [word(1,8)]
        if number==20:return [word(1,12,'()[]{}')]
        if number==32:return [word(0,12,'()')]
        if number==17:return [word(1,3,'23456789')]
        if number in (22,51):return [rng.randint(1,5)]
        if number==394:return [f'{rng.randint(1,4)}[{word(1,3)}{rng.randint(1,3)}[{word(1,2)}]]']
        return [rng.randint(1,15 if number==70 else 10 if number==118 else 60)]
    if number in (438,76,1143,72):
        return [word(0 if number==72 else 1,9,'abAB' if number==76 else 'abc'),word(0 if number==72 else 1,5,'abAB' if number==76 else 'abc')]
    if number in (56,207):
        if number==56:
            return [[sorted([rng.randint(0,10),rng.randint(0,10)]) for _ in range(n)]]
        count=rng.randint(1,7); pairs=rng.sample([(i,j) for i in range(count) for j in range(count)],rng.randint(0,min(10,count*count)))
        return [count,[list(p) for p in pairs]]
    if number in (73,54,48,240,74,994,64,200,79):
        m=rng.randint(1,4);cols=m if number==48 else rng.randint(1,4)
        rows=[[rng.randint(0,5) for _ in range(cols)] for _ in range(m)]
        if number==240:rows=[[i*2+j*3-10 for j in range(cols)] for i in range(m)]
        if number==74:
            values=sorted(rng.sample(range(-50,51),m*cols));rows=[values[i*cols:(i+1)*cols] for i in range(m)]
        if number in (240,74):return [rows,rng.choice([rows[rng.randrange(m)][rng.randrange(cols)],rng.randint(-50,50)])]
        if number==994:rows=[[rng.randrange(3) for _ in range(cols)] for _ in range(m)]
        if number==200:rows=[[rng.choice('01') for _ in range(cols)] for _ in range(m)]
        if number==79:return [[[rng.choice('AB') for _ in range(cols)] for _ in range(m)],word(1,6,'AB')]
        return [rows]
    if number in (160,206,234,141,142,21,2,19,24,25,138,23):
        values=ints(0 if number in (206,141,142,24,138) else 1,8,0,9)
        if number==160:
            left,right=ints(1,4,1,9),ints(1,4,1,9)
            if rng.randrange(2):
                tail=ints(1,4,1,9);return [left+tail,right+tail,len(left),len(right)]
            return [left,right,-1,-1]
        if number==234 and rng.randrange(2):values=values+values[::-1]
        if number in (141,142):return [values,rng.randrange(-1,len(values)) if values else -1]
        if number==21:return [sorted(values),sorted(ints(0,8))]
        if number==2:
            right=ints(1,8,0,9)
            if len(values)>1:values[-1]=rng.randint(1,9)
            if len(right)>1:right[-1]=rng.randint(1,9)
            return [values,right]
        if number in (19,25):return [values,rng.randint(1,len(values))]
        if number==138:return [values,[rng.randrange(-1,len(values)) for _ in values]]
        if number==23:return [[sorted(ints(0,6)) for _ in range(n)]]
        return [values]
    if number in (94,104,226,101,543,102,108,98,230,199,114,105,437,236,124):
        if number==108:return [sorted(rng.sample(range(-50,51),n))]
        if number==105:
            root=__import__('judge.reference',fromlist=['tree']).tree(random_tree(rng,n,unique=True))
            pre,ino,_=traversals(root);return [pre,ino]
        minimum=2 if number==236 else 1 if number in (98,101,543,230,124) else 0
        values=random_tree(rng,rng.randint(minimum,9),unique=number==236,bst=number==230)
        if number==230:
            # Kth BST input values must be in [0, 10000].
            values=[x+100 if x is not None else None for x in values]
            return [values,rng.randint(1,len([x for x in values if x is not None]))]
        if number==437:return [values,rng.randint(-5,5)]
        if number==236:return [values,*rng.sample([x for x in values if x is not None],2)]
        return [values]
    if number in (146,155,208,295):
        operations=[]
        if number==146:
            for _ in range(rng.randint(1,25)):
                operations.append(['put',rng.randrange(5),rng.randint(0,10)] if rng.randrange(2) else ['get',rng.randrange(5)])
            return [rng.randint(1,4),operations]
        if number==208:
            return [[[rng.choice(['insert','search','startsWith']),word(1,5)] for _ in range(rng.randint(1,20))]]
        count=0
        for _ in range(rng.randint(1,25)):
            command=rng.choice(['push','pop','top','getMin']) if number==155 else rng.choice(['addNum','findMedian'])
            if not count:command='push' if number==155 else 'addNum'
            if command in ('push','addNum'):operations.append([command,rng.randint(-20,20)]);count+=1
            else:
                operations.append([command]);count-=command=='pop'
        return [operations]
    if number in (35,34,33,153,4):
        if number==4:return [sorted(ints(0,8)),sorted(ints(1,8))]
        values=sorted(rng.sample(range(-30,31),n))
        if number==34:values=sorted(ints(0,9))
        if number in (33,153):
            pivot=rng.randrange(len(values));values=values[pivot:]+values[:pivot]
        if number==153:return [values]
        return [values,rng.choice(values+[rng.randint(-30,30)]) if values else 0]
    if number==39:return [rng.sample(range(2,12),rng.randint(1,6)),rng.randint(1,20)]
    if number==322:return [rng.sample(range(1,15),rng.randint(1,5)),rng.randint(0,50)]
    if number==139:return [word(1,10),sorted({word(1,4) for _ in range(8)})]
    if number==62:return [rng.randint(1,8),rng.randint(1,8)]
    raise KeyError(f'未定义随机用例：{number}')


def chain_tree(count, value=1, direction='right', unique=False):
    if not count:return []
    values=[0 if unique else value]
    for i in range(1,count):
        v=i if unique else value
        values.extend([None,v] if direction=='right' else [v,None])
    if values[-1] is None:values.pop()
    return values


def pressure(number):
    """One or more upper-dimension cases; every value remains within题意."""
    arrays = {
        128:list(range(100000)),283:[0,1]*5000,11:[10000]*100000,15:[0]*3000,42:[100000]+[0]*19998+[100000],
        53:[-10000]*100000,238:[1]*100000,41:list(range(1,100001)),206:list(range(5000)),234:[1]*100000,
        24:list(range(100)),148:[50000-i for i in range(50000)],121:[10000-i%10001 for i in range(100000)],
        55:[1]*10000,45:[1]*10000,198:[400]*100,300:list(range(2500)),152:[-1]*20000,
        416:[100]*200,136:list(chain.from_iterable([i,i] for i in range(14999)))+[-30000],
        169:[-10**9]*25001+[10**9]*24999,75:[2,1,0]*100,31:[100]*100,287:list(range(1,100001))+[100000],
        739:[100]*99999+[100],84:[10000]*100000,46:[-3,-2,-1,0,1,2],78:list(range(10)),
    }
    if number in arrays:return [[arrays[number]]]
    if number==1:return [[[10**9]*9998+[-1,-2],-3]]
    if number==49:return [[['a'*100]*10000]]
    if number==3:return [['abc ' * 25000]]
    if number==438:return [['a'*30000,'a'*30000],['a'*30000,'a']]
    if number==560:return [[[0]*20000,0]]
    if number==239:return [[[10000-i%20001 for i in range(100000)],50000]]
    if number==76:return [['A'*99999+'B','A'*99999+'B']]
    if number==56:return [[[[0,10000] for _ in range(10000)]]]
    if number==189:return [[list(range(100000)),100000-1]]
    if number==73:return [[[[0 if (i,j)==(199,199) else 2147483647 for j in range(200)] for i in range(200)]]]
    if number==54:return [[[[i*10+j for j in range(10)] for i in range(10)]]]
    if number==48:return [[[[i*20+j for j in range(20)] for i in range(20)]]]
    if number==240:return [[[[i*300+j for j in range(300)] for i in range(300)],89999]]
    if number==160:return [[[1]*30000,[2]*15000+[1]*15000,15000,15000]]
    if number in (141,142):return [[[100000]*10000,9999],[[100000]*10000,-1]]
    if number==21:return [[[100]*50,[-100]*50]]
    if number==2:return [[[9]*100,[1]],[[9]*100,[9]*100]]
    if number==19:return [[[100]*30,30]]
    if number==25:return [[[1000]*5000,4999],[[i%1001 for i in range(5000)],5000]]
    if number==138:return [[[10000]*1000,list(range(999,-1,-1))]]
    if number==23:return [[[[i] for i in range(10000)]],[[list(range(-250,250)) for _ in range(20)]]]
    if number==146:return [[3000,[['put',i%10001,i%100001] if i%2==0 else ['get',(i-1)%10001] for i in range(200000)]]]
    tree_sizes={94:100,104:10000,226:100,101:1000,543:10000,102:2000,98:10000,230:10000,199:100,114:2000,437:1000,236:100000,124:30000}
    if number in tree_sizes:
        count=tree_sizes[number];values=chain_tree(count,value=-1 if number==124 else 1,unique=number in (98,230,236))
        if number==230:return [[values,count]]
        if number==236:return [[values,count//2,count-1]]
        if number==437:return [[values,1]]
        return [[values]]
    if number==108:return [[list(range(-5000,5000))]]
    if number==105:return [[list(range(3000)),list(range(3000))]]
    if number==200:return [[[list('1'*300) for _ in range(300)]]]
    if number==994:return [[[[2]+[1]*9]+[[1]*10 for _ in range(9)]]]
    if number==207:return [[2000,([[i,i-1] for i in range(1,2000)]+[[i,i-2] for i in range(2,2000)]+[[i,i-3] for i in range(3,2000)])[:5000]]]
    if number==208:return [[[['insert','a'*2000],['search','a'*2000]]+[['search','a'] if i%2 else ['startsWith','a'] for i in range(29998)]]]
    if number==17:return [['9999']]
    if number==39:return [[list(range(11,41)),40]]
    if number==22:return [[8]]
    if number==79:return [[[list('AAAAAA') for _ in range(6)],'A'*14+'B']]
    if number==131:return [['a'*16]]
    if number==51:return [[9]]
    if number==35:return [[list(range(-5000,5000)),10000]]
    if number==74:return [[[[i*100+j for j in range(100)] for i in range(100)],9999]]
    if number==34:return [[[10**9]*100000,10**9]]
    if number==33:return [[list(range(2500,5000))+list(range(2500)),4999]]
    if number==153:return [[list(range(1,5000))+[0]]]
    if number==4:return [[list(range(-1000,0)),list(range(1000))]]
    if number==20:return [['('*5000+')'*5000]]
    if number==155:return [[[['push',-2147483648]]+[['getMin'] for _ in range(29999)]]]
    if number==394:return [['300[300[a]]100[100[a]]'],['a'*30]]
    if number==215:return [[[10000-i%20001 for i in range(100000)],100000]]
    if number==347:return [[[0]*50001+[i%10000+1 for i in range(49999)],1]]
    if number==295:return [[[['addNum',-100000 if i%2 else 100000] if i%3 else ['findMedian'] for i in range(1,50001)]]]
    if number==763:return [['a'*500]]
    if number==70:return [[45]]
    if number==118:return [[30]]
    if number==279:return [[10000],[9999]]
    if number==322:return [[[1,7,17,71,127,251,503,997,1999,3001,5003,9973],10000]]
    if number==139:return [['a'*299+'b',['a'*i for i in range(1,21)]+['z'+''.join('b' if (i>>bit)&1 else 'a' for bit in range(10)) for i in range(980)]]]
    if number==32:return [['('*15000+')'*15000]]
    if number==62:return [[100,1],[17,17]]
    if number==64:return [[[[200]*200 for _ in range(200)]]]
    if number==5:return [['a'*1000]]
    if number==1143:return [['a'*1000,'a'*999+'b']]
    if number==72:return [['a'*500,'b'*500]]
    raise KeyError(f'未定义压力用例：{number}')


def endpoint_cases(number):
    """Explicit numeric/alphabet endpoints, in addition to size pressure.

    Inputs with extra invariants are individually constructed rather than
    replacing values blindly (which would invalidate e.g. 2-sum uniqueness).
    """
    from .validation import ARRAYS,TREES
    plain={128,283,11,42,53,41,206,148,739,84,121,198,300,75,31}
    if number in plain:
        minimum,maximum,lo,hi=ARRAYS[number]
        count=max(minimum,3)
        return [[[lo]*count],[[hi]*count],[[lo,hi,lo]]]
    if number in TREES:
        _,_,lo,hi=TREES[number]
        if number==230:return [[[0,None,10000],2]]
        if number==236:return [[[0,lo,hi],lo,hi]]
        if number==437:return [[[0,lo,hi],0]]
        return [[[lo,lo,lo]],[[hi,hi,hi]],[[0,lo,hi]]]
    extra={
        1:[[[-10**9,0],-10**9],[[0,10**9],10**9]],
        49:[[['az','za','zz','z','']]],
        15:[[[-100000,0,100000]]],
        3:[['~0aA ~']],438:[['zzaz','zz']],560:[[[-1000,1000],-10**7],[[1000,-1000],10**7]],
        239:[[[-10000,10000,-10000],1],[[-10000,10000,-10000],3]],
        76:[['aAzZ','AZ'],['ZZ','ZZZ']],56:[[[[0,0],[10000,10000],[0,10000]]]],
        189:[[[-2**31,2**31-1],0],[[-2**31,2**31-1],100000]],
        238:[[[-30,30]],[[0,-30,30]]],
        73:[[[[-2**31,0],[1,2**31-1]]]],54:[[[[-100,100]]]],48:[[[[-1000,1000],[1000,-1000]]]],
        240:[[[[-10**9,0],[0,10**9]],10**9]],74:[[[[-10000,0,10000]],-10000]],
        160:[[[100000],[100000],-1,-1],[[100000],[100000],0,0]],
        234:[[[0,9,0]],[[9,0,9,9]]],141:[[[-100000,100000],-1]],142:[[[-100000,100000],1]],
        19:[[[0,100],1]],24:[[[100,0,100]]],25:[[[0,1000,0],2]],
        138:[[[-10000,10000],[1,0]]],23:[[[[-10000,0],[10000]]]],
        108:[[[-10000,0,10000]]],105:[[[0,-3000,3000],[-3000,0,3000]]],
        46:[[[-10,0,10]]],78:[[[-10,0,10]]],
        79:[[[['a']],'A'],[[['z']],'z']],131:[['zz'],['az']],
        35:[[[-10000,0,10000],-10000],[[-10000,0,10000],10000]],
        34:[[[-10**9,0,10**9],-10**9],[[-10**9,0,10**9],10**9]],
        33:[[[0,10000,-10000],-10000],[[0,10000,-10000],1]],153:[[[0,5000,-5000]]],
        4:[[[-10**6],[10**6]],[[10**6],[10**6]]],
        215:[[[-10000,10000,-10000],1],[[-10000,10000,-10000],3]],
        347:[[[-10000,-10000,10000],1]],
        55:[[[100000,0]],[[0,100000]]],45:[[[1000,0]]],
        763:[['zaz']],322:[[[1,2**31-1],1]],139:[['z'*20,['z'*20]]],
        152:[[[-10,-10]],[[10,0,-10]]],416:[[[100]],[[1,100,99]]],
        5:[['aA0Aa'],['00']],1143:[['az','za']],72:[['az','za']],
        136:[[[-30000,30000,-30000]]],169:[[[10**9,-10**9,10**9]]],
    }
    return extra.get(number,[])


def suite(number, seed=None, random_count=128):
    rng=random.Random(2026102900+number if seed is None else seed)
    cases=[dict(args=args,kind='sample' if i<2 else 'boundary',label=f'公开样例 {i+1}' if i<2 else f'定向边界 {i-1}') for i,args in enumerate(EDGES[number])]
    cases += [dict(args=args,kind='boundary',label=f'值域/字符端点 {i+1}') for i,args in enumerate(endpoint_cases(number))]
    cases += [dict(args=random_case(number,rng),kind='random',label=f'固定随机 {i+1}') for i in range(random_count)]
    cases += [dict(args=args,kind='pressure',label=f'上界压力 {i+1}') for i,args in enumerate(pressure(number))]
    return cases
