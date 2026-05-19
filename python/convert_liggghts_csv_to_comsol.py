from __future__ import annotations
import argparse, csv
UM_PER_CM=10000.0

def pick(row,*names):
    for n in names:
        if n in row and row[n] not in ('',None): return row[n]
    raise KeyError(names)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--mode', default='2d')
    ap.add_argument('--output', default='D:/CodexProjects/scripts/comsol_particles.csv')
    args=ap.parse_args()
    with open(args.input, newline='') as f:
        sample=f.read(4096); f.seek(0)
        dialect=csv.Sniffer().sniff(sample, delimiters=', \t')
        reader=csv.DictReader(f, dialect=dialect)
        out=[]
        counts={1:0,2:0}
        for r in reader:
            typ=int(float(pick(r,'type','Type')))
            x=float(pick(r,'x','Points:0','Points_0'))*UM_PER_CM
            y=float(pick(r,'y','Points:1','Points_1'))*UM_PER_CM
            rad=float(pick(r,'radius','Radius'))*UM_PER_CM
            shape='Al' if typ==1 else ('DL' if rad>30 else 'DS')
            counts[typ]=counts.get(typ,0)+1
            out.append({'id':pick(r,'id','ID'),'type':typ,'shape':shape,'x_um':x,'y_um':y,'r_um':rad})
    with open(args.output,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','type','shape','x_um','y_um','r_um'])
        w.writeheader(); w.writerows(out)
    print(f'[OK] wrote {args.output} rows={len(out)} counts={counts}')

if __name__ == '__main__': main()
