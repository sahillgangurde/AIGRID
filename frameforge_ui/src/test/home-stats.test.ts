import {describe,it,expect} from 'vitest';
import {homeStats,countAtProgress} from '@/lib/home-stats';
describe('Opening homepage counters',()=>{
 it('counts filmmakers from zero to 1,053',()=>{expect(countAtProgress(homeStats[0]?.value??-1,0)).toBe(0);expect(countAtProgress(homeStats[0]?.value??-1,1)).toBe(1053);});
 it('ends at 179 films',()=>{expect(countAtProgress(homeStats[1]?.value??-1,1)).toBe(179);});
 it('ends at 7 open briefs',()=>{expect(countAtProgress(homeStats[2]?.value??-1,1)).toBe(7);});
 it('ends at 1 listing',()=>{expect(countAtProgress(homeStats[3]?.value??-1,1)).toBe(1);});
 it('shows intermediate increasing counts without exceeding the total',()=>{expect(countAtProgress(1053,.25)).toBeGreaterThan(0);expect(countAtProgress(1053,.5)).toBeGreaterThan(countAtProgress(1053,.25));expect(countAtProgress(1053,2)).toBe(1053);});
});