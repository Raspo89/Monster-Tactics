import csv,json,collections
from pathlib import Path
base=Path('/workspace/scratch/d96bc0fd2488/races-site/.sites-checkout')
rows=list(csv.DictReader(open(base/'reference/native-rules/table-3189a0.txt')))
mapping={x['eRaceType enum']+'_'+x['']:x for x in csv.DictReader(open(base/'reference/native-rules/table-33e4f8.txt')) if x['eRaceType enum']}
classes={'CT_FIGHTER':('F','fighter','warrior'),'CT_RANGER':('R','rogue','archer'),'CT_MAGE':('M','spellcaster','mage'),'CT_ARTIL':('A','artillery','artillery')}
racekeys=['human','elf','orc','zombie','lizard','dwarf','minotaur','werewolf','golem','elemental','cyclops','skeleton','imp','spectre','vampire']
def race(x):return 'zombie' if x['Race']=='RT_UNDEAD' else x['Race'][3:].lower()
valid=[(i+2,x) for i,x in enumerate(rows) if x['Race'] and x['Name'] and x['Health'] and float(x['Health'])>0 and x['Texture Name'].isdigit() and int(x['Texture Name'])<12 and x['Ability']!='AT_NONE']
chosen=[]
def add(item):
 if item not in chosen:chosen.append(item)
for name in ['Duron','Edric','Rickard','Shody']:
 add(next(x for x in valid if x[1]['Name']==name and x[1]['Race']=='RT_HUMAN'))
# Cover every actual active ability, selecting underrepresented races/classes at sensible costs.
for ability in sorted(set(x[1]['Ability'] for x in valid), key=lambda a:sum(x[1]['Ability']==a for x in valid)):
 if any(x[1]['Ability']==ability for x in chosen):continue
 pool=[x for x in valid if x[1]['Ability']==ability]
 def score(item):
  _,x=item;r=race(x)
  count=sum(race(y)==r for _,y in chosen)
  clcount=sum(race(y)==r and y['Class']==x['Class'] for _,y in chosen)
  return (count,clcount,int(x['Mojo']),-int(x['Power']),-int(x['Health']),item[0])
 add(min(pool,key=score))
# Two real ability monsters per available class and race; diversify active effects locally.
for r in racekeys:
 for cl in classes:
  while sum(race(x)==r and x['Class']==cl for _,x in chosen)<2:
   pool=[item for item in valid if race(item[1])==r and item[1]['Class']==cl and item not in chosen]
   if not pool:break
   used={x['Ability'] for _,x in chosen if race(x)==r}
   add(min(pool,key=lambda item:(item[1]['Ability'] in used,int(item[1]['Mojo']),-int(item[1]['Power']),-int(item[1]['Health']),item[0])))
plan=[]
for line,x in sorted(chosen,key=lambda item:(racekeys.index(race(item[1])),item[0])):
 r=race(x);cl,role,combat=classes[x['Class']];m=mapping[x['Race']+'_'+cl]
 plan.append({'id':f'NA_{r}_{line:04}','race':r,'row':line,'native':x,'ability':x['Ability'],'model':('undead' if r=='zombie' else r)+'_'+role,'skin':int(x['Texture Name']),'combatClass':combat,'folder':m['Folder Name'],'sourceModel':m['Model']})
assert len(plan)<=160
assert set(x['Ability'] for _,x in valid)==set(x['ability'] for x in plan)
(base/'src/data/ability-card-plan.json').write_text(json.dumps(plan,indent=2))
print('PLAN',len(plan),'abilities',len(set(x['ability'] for x in plan)))
print(collections.Counter(x['race'] for x in plan));print('models',len(set(x['model'] for x in plan)))
