exec(open('/workspace/scratch/d96bc0fd2488/pov-review/bake-views.py').read().split("if __name__")[0])
result={}
for key in b.MAN:
 for side in ['back','front']:
  angle=np.deg2rad(54.25);b.EYE=np.array([0,np.sin(angle),np.cos(angle)*(1 if side=='back' else -1)]);b.RIGHT=np.cross([0,1,0],b.EYE);b.RIGHT/=np.linalg.norm(b.RIGHT);b.UP=np.cross(b.EYE,b.RIGHT)
  model=json.loads((b.ROOT/b.MAN[key]['json']).read_text());xy=[]
  for clip in ['idle','walk','attack']:
   count=len(b.AN['clips'][clip]['frames'])
   for col in range(8):
    mm=b.pose_matrices(model,clip,round(col*(count-1)/7))
    for g in model['groups']:
     v=b.skin(model,g,mm);xy.append(np.c_[v@b.RIGHT,v@b.UP])
  xy=np.concatenate(xy);lo=xy.min(0);hi=xy.max(0);scale=min(160*.88/(hi[0]-lo[0]),180*.88/(hi[1]-lo[1]));center=(lo+hi)/2;verts=np.concatenate([np.array(g.get('idlePositions') or g['positions']).reshape(-1,3) for g in model['groups']]);height=float(np.ptp(verts[:,1]));result[key+'-'+side]={'originX':float((80-center[0]*scale)/160),'originY':float((90+center[1]*scale)/180),'pixelsPerUnit':float(scale),'height':height}
Path('/workspace/scratch/d96bc0fd2488/pov-site/.sites-checkout/src/data/pov-sprites.json').write_text(json.dumps(result,indent=2))
