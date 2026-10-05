const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'proofs',name+'.json')));
const deployment=read('deployment');
assert.equal(deployment.chain_id,61999);
assert.equal(deployment.source_sha256,digest(fs.readFileSync(path.join(root,'contracts/mutual_slot.py'))));
assert.equal(deployment.exact_source_match,true);
assert.equal(deployment.transactions.length,5);
const expected={displacement:{ada:'field',ben:'lab',cy:null},ties:{ada:'lab',ben:null,cy:'field'},rejection:{ada:null,ben:'lab',cy:null},uncertain:{}};
function stable(policy,prefs,matching){
 for(const applicant of policy.applicants){
  const current=matching[applicant];
  if(current!==null && (!prefs[applicant].includes(current)||!prefs[current].includes(applicant)))return false;
  for(const slot of prefs[applicant]){
   if(!prefs[slot].includes(applicant)||current===slot)continue;
   if(current!==null && prefs[applicant].indexOf(current)<prefs[applicant].indexOf(slot))continue;
   const occupants=policy.applicants.filter(other=>matching[other]===slot);
   const capacity=policy.slots.find(item=>item.id===slot).capacity;
   if(occupants.length<capacity||occupants.some(other=>prefs[slot].indexOf(applicant)<prefs[slot].indexOf(other)))return false;
  }
 }
 return policy.slots.every(slot=>policy.applicants.filter(a=>matching[a]===slot.id).length<=slot.capacity);
}
function assignments(policy){
 let result=[{}];
 for(const applicant of policy.applicants)result=result.flatMap(row=>[null,...policy.slots.map(slot=>slot.id)].map(slot=>({...row,[applicant]:slot})));
 return result;
}
for(const tx of deployment.transactions){
 const receipt=read(tx.label+'-receipt');
 assert.equal(receipt.hash,tx.hash);
 assert.equal(receipt.status_name||receipt.statusName,'FINALIZED');
 assert.equal(receipt.result_name,'MAJORITY_AGREE');
 assert(['SUCCESS','FINISHED_WITH_RETURN'].includes(receipt.txExecutionResultName||receipt.consensus_data.leader_receipt[0].execution_result));
 assert(Object.values(receipt.consensus_data.votes).filter(item=>item==='agree').length>=3);
 if(tx.action==='deploy')continue;
 const proof=read(tx.label),state=proof.state;
 assert.equal(proof.contract_address,deployment.contract_address);
 assert.equal(proof.source_sha256,deployment.source_sha256);
 assert.equal(receipt.to_address.toLowerCase(),deployment.contract_address.toLowerCase());
 assert.deepEqual(state.rounds.at(-1).result.matching,expected[tx.label]);
 const calldata=receipt.data.calldata.readable;
 assert(calldata.includes(state.rounds.at(-1).url));
 assert(calldata.includes(state.rounds.at(-1).sha256));
 for(const row of state.rounds){
  const body=fs.readFileSync(path.join(root,'records',new URL(row.url).pathname.split('/').pop()));
  assert.equal(digest(body),row.sha256);
  assert(row.url.startsWith('https://raw.githubusercontent.com/'+state.policy.source_repository+'/'+deployment.fixture_revision+'/records/'));
  const ids=[...state.policy.applicants,...state.policy.slots.map(item=>item.id)];
  assert.deepEqual(row.report.profiles.map(item=>item.id),ids);
  for(const profile of row.report.profiles){
   const candidates=state.policy.applicants.includes(profile.id)?state.policy.slots.map(item=>item.id):state.policy.applicants;
   const all=[...profile.tiers.flat(),...profile.rejected,...profile.unknown];
   assert.equal(new Set(all).size,all.length);assert.deepEqual(all.slice().sort(),candidates.slice().sort());
   if(profile.quote)assert(body.toString().includes(profile.quote));
   if(!profile.unknown.length)assert(profile.quote.length>=12);
  }
  const unresolved=row.report.profiles.some(item=>item.unknown.length);
  assert.equal(row.result.status,unresolved?'REVIEW':'MATCHED');
  if(unresolved){assert.deepEqual(row.result.matching,{});assert.deepEqual(row.result.proposals,[]);continue;}
  const prefs=Object.fromEntries(row.report.profiles.map(item=>[item.id,item.tiers.flat()]));
  assert(stable(state.policy,prefs,row.result.matching));
  assert.deepEqual(row.result.blocking_pairs,[]);
  assert.deepEqual(row.result.unmatched,state.policy.applicants.filter(a=>row.result.matching[a]===null));
  const rank=(a,slot)=>slot===null?prefs[a].length+1:prefs[a].indexOf(slot);
  for(const alternative of assignments(state.policy).filter(candidate=>stable(state.policy,prefs,candidate)))
   assert(state.policy.applicants.every(a=>rank(a,row.result.matching[a])<=rank(a,alternative[a])));
  const cursors=Object.fromEntries(state.policy.applicants.map(a=>[a,0]));
  const held=Object.fromEntries(state.policy.slots.map(item=>[item.id,[]]));
  for(const proposal of row.result.proposals){
   assert(!Object.values(held).flat().includes(proposal.applicant));
   assert.equal(prefs[proposal.applicant][cursors[proposal.applicant]++],proposal.slot);
   let removed=proposal.applicant;
   if(prefs[proposal.slot].includes(proposal.applicant)){
    held[proposal.slot].push(proposal.applicant);
    held[proposal.slot].sort((a,b)=>prefs[proposal.slot].indexOf(a)-prefs[proposal.slot].indexOf(b));
    removed=held[proposal.slot].length>state.policy.slots.find(item=>item.id===proposal.slot).capacity?held[proposal.slot].pop():null;
   }
   assert.equal(proposal.removed,removed);
  }
  assert.deepEqual(Object.fromEntries(state.policy.applicants.map(a=>[a,Object.keys(held).find(slot=>held[slot].includes(a))||null])),row.result.matching);
 }
 console.log('VERIFIED',tx.label,JSON.stringify(state.rounds.at(-1).result.matching));
}
console.log('Verified five finalized receipts, source partitions, proposal traces and independently enumerated stability.');
