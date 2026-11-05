import sys,re
def load(p):
    t=open(p).read(); v=[tuple(map(float,m)) for m in re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)',t)]
    return [v[i:i+3] for i in range(0,len(v),3)]
for p in sys.argv[1:]:
    tr=load(p)
    if not tr: print(f'{p}: 빈 결과(부피 0)'); continue
    V=sum((a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])) for a,b,c in tr)/6
    pts=[q for t in tr for q in t]; lo=[min(q[i] for q in pts) for i in range(3)]; hi=[max(q[i] for q in pts) for i in range(3)]
    print(f'{p}: 부피 {V:.1f} mm3, x {lo[0]:.1f}~{hi[0]:.1f}, y {lo[1]:.1f}~{hi[1]:.1f}, z {lo[2]:.1f}~{hi[2]:.1f}')
