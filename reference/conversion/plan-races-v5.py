import csv,json
from pathlib import Path
base=Path('/workspace/scratch/d96bc0fd2488/races-site/.sites-checkout');rows=list(csv.DictReader(open(base/'reference/native-rules/table-3189a0.txt')))
mapping={x['eRaceType enum']+'_'+x['']:x for x in csv.DictReader(open(base/'reference/native-rules/table-33e4f8.txt')) if x['eRaceType enum']}
classes={'CT_FIGHTER':('F','fighter','warrior'),'CT_RANGER':('R','rogue','archer'),'CT_MAGE':('M','spellcaster','mage'),'CT_ARTIL':('A','artillery','artillery')}
plan=[]
for race in ['human','elf','orc','zombie','lizard','dwarf','minotaur','werewolf','golem','elemental','cyclops','skeleton','robot','imp','spectre','vampire']:
 valid=[(i+3,x) for i,x in enumerate(rows) if x['Race']=='RT_'+('UNDEAD' if race=='zombie' else race.upper()) and x['Name'] and x['Health'] and float(x['Health'])>0 and x['Power'] and float(x['Power'])>0 and x['Ability']=='AT_NONE' and x['Texture Name'].isdigit() and int(x['Texture Name'])<12]
 valid.sort(key=lambda item:(int(item[1]['Power'])<=0,int(item[1]['Mojo']),-int(item[1]['Power']),-int(item[1]['Health'])))
 chosen=[]
 for cl in classes:
  own=[x for x in valid if x[1]['Class']==cl];chosen+=own[:2]
 for row in valid:
  if len(chosen)>=8:break
  if row not in chosen:chosen.append(row)
 for n,(line,x) in enumerate(chosen,1):
  cl,role,combat=classes[x['Class']];m=mapping[x['Race']+'_'+cl]
  plan.append({'id':f'CM_{race}_{n:02}','race':race,'row':line,'native':x,'model':('undead' if race=='zombie' else race)+'_'+role,'skin':int(x['Texture Name']),'combatClass':combat,'folder':m['Folder Name'],'sourceModel':m['Model']})
(base/'src/data/race-card-plan.json').write_text(json.dumps(plan,indent=2));print('planned',len(plan),'cards',len(set(x['model'] for x in plan)),'models')
