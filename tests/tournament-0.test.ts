import {it,expect} from 'vitest';
import {benchmark} from './benchmark';
it('paired identical-seed AI comparison part 1',async()=>{const result=await benchmark(0);for(const r of Object.values(result) as any[]){expect(r.wins+r.losses+r.draws).toBe(13);expect(r.draws).toBe(0);}},600000);
