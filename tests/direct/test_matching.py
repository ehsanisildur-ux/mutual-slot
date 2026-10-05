import ast
import hashlib
import itertools
import json
import re
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
POLICY=json.loads((ROOT/'config/policy.json').read_text())
DOCS={name:(ROOT/'records'/f'{name}.md').read_bytes() for name in ['displacement','ties','rejection','uncertain']}
TIERS={
 'displacement':[[['lab'],['field']],[['lab'],['field']],[['field'],['lab']],[['ben'],['ada'],['cy']],[['ada'],['cy'],['ben']]],
 'ties':[[['lab','field']],[['lab']],[['field']],[['ada','ben']],[['cy'],['ada']]],
 'rejection':[[['lab']],[['field'],['lab']],[],[['ben']],[['ada']]],
 'uncertain':[[],[['lab'],['field']],[['field'],['lab']],[['ben'],['ada'],['cy']],[['ada'],['cy'],['ben']]]}
def source(name):return f"https://raw.githubusercontent.com/ehsanisildur-ux/mutual-slot/{'a'*40}/records/{name}.md",hashlib.sha256(DOCS[name]).hexdigest()
def report(name):
    rows=[]
    for i,(identity,tiers) in enumerate(zip(['ada','ben','cy','lab','field'],TIERS[name])):
        tiers=json.loads(json.dumps(tiers))
        candidates=['lab','field'] if i<3 else ['ada','ben','cy']
        unknown=candidates if name=='uncertain' and i==0 else []
        used=[item for tier in tiers for item in tier]
        rows.append({'id':identity,'tiers':tiers,'rejected':[item for item in candidates if item not in used and item not in unknown],'unknown':unknown,'quote':DOCS[name].decode().splitlines()[i+1]})
    return {'profiles':rows}
def mock(vm,name,leader=None,independent=None,anchors=None,changed=None):
    vm.clear_mocks()
    vm.mock_web(re.escape(source(name)[0]),{'status':200,'body':changed or DOCS[name]})
    vm.mock_llm(r'.*MUTUALSLOT-LEADER.*',json.dumps(leader or report(name)))
    vm.mock_llm(r'.*MUTUALSLOT-VALIDATOR.*',json.dumps(independent or report(name)))
    vm.mock_llm(r'.*MUTUALSLOT-ANCHORS.*',json.dumps({'valid':anchors if anchors is not None else [True]*5}))
@pytest.fixture
def market(direct_deploy):return direct_deploy(str(ROOT/'contracts/mutual_slot.py'),json.dumps(POLICY))
def run(c,vm,name):mock(vm,name);c.match(*source(name));return c.get_state()['rounds'][-1]['result']
def test_displacement(market,direct_vm):
    result=run(market,direct_vm,'displacement')
    assert result['matching']=={'ada':'field','ben':'lab','cy':None}
    assert len(result['proposals'])==5
    assert result['blocking_pairs']==[]
def test_tie_refinement(market,direct_vm):
    result=run(market,direct_vm,'ties')
    assert result['matching']=={'ada':'lab','ben':None,'cy':'field'}
    assert result['unmatched']==['ben']
def test_nonreciprocal_exclusion(market,direct_vm):
    result=run(market,direct_vm,'rejection')
    assert result['matching']=={'ada':None,'ben':'lab','cy':None}
    assert 'field' not in result['matching'].values()
def test_unknown_prevents_assignment(market,direct_vm):
    result=run(market,direct_vm,'uncertain')
    assert result['status']=='REVIEW' and result['matching']=={}
def test_multi_seat_capacity(direct_deploy,direct_vm):
    policy=json.loads(json.dumps(POLICY));policy['slots'][0]['capacity']=2
    c=direct_deploy(str(ROOT/'contracts/mutual_slot.py'),json.dumps(policy))
    assert run(c,direct_vm,'displacement')['matching']=={'ada':'lab','ben':'lab','cy':'field'}
def test_duplicate_does_not_append(market,direct_vm):
    run(market,direct_vm,'ties')
    with direct_vm.expect_revert('Duplicate record'):market.match(*source('ties'))
    assert len(market.get_state()['rounds'])==1
def test_distinct_batches(market,direct_vm):
    for name in TIERS:run(market,direct_vm,name)
    assert len(market.get_state()['rounds'])==4
def test_validator_agrees(market,direct_vm):
    run(market,direct_vm,'displacement');assert direct_vm.run_validator() is True
def test_validator_rejects_rank_change(market,direct_vm):
    run(market,direct_vm,'displacement')
    independent=report('displacement');independent['profiles'][0]['tiers'].reverse()
    mock(direct_vm,'displacement',independent=independent)
    assert direct_vm.run_validator() is False
def test_validator_rejects_acceptance_change(market,direct_vm):
    run(market,direct_vm,'ties')
    independent=report('ties');independent['profiles'][1]['tiers'].append(['field']);independent['profiles'][1]['rejected']=[]
    mock(direct_vm,'ties',independent=independent);assert direct_vm.run_validator() is False
def test_validator_rejects_unknown_change(market,direct_vm):
    run(market,direct_vm,'uncertain')
    independent=report('uncertain');independent['profiles'][0]['unknown']=[];independent['profiles'][0]['rejected']=['lab','field']
    mock(direct_vm,'uncertain',independent=independent);assert direct_vm.run_validator() is False
def test_validator_tie_order_normalizes(market,direct_vm):
    run(market,direct_vm,'ties')
    independent=report('ties');independent['profiles'][0]['tiers'][0].reverse()
    mock(direct_vm,'ties',independent=independent);assert direct_vm.run_validator() is True
def test_validator_anchor_relevance(market,direct_vm):
    run(market,direct_vm,'ties');mock(direct_vm,'ties',anchors=[True]*4+[False]);assert direct_vm.run_validator() is False
def test_validator_hash_binding(market,direct_vm):
    run(market,direct_vm,'ties');mock(direct_vm,'ties',changed=DOCS['ties']+b'changed');assert direct_vm.run_validator() is False
@pytest.mark.parametrize('kind',['duplicate','omission','forged-quote'])
def test_invalid_leader(market,direct_vm,kind):
    bad=report('ties')
    if kind=='duplicate':bad['profiles'][0]['tiers'][0]=['lab','lab']
    if kind=='omission':bad['profiles'][0]['tiers'][0]=['lab']
    if kind=='forged-quote':bad['profiles'][0]['quote']='A fabricated quote absent from the actual record.'
    mock(direct_vm,'ties',leader=bad)
    with direct_vm.expect_revert():market.match(*source('ties'))
@pytest.mark.parametrize('url',['https://example.com/preferences.md',f"https://raw.githubusercontent.com/other/mutual-slot/{'a'*40}/records/ties.md"])
def test_fixed_publisher(market,direct_vm,url):
    with direct_vm.expect_revert('pinned publisher'):market.match(url,'a'*64)
def test_exhaustive_small_market_stability_and_optimality():
    # Extract only the pure solver helpers; independently enumerate all assignments.
    tree=ast.parse((ROOT/'contracts/mutual_slot.py').read_text())
    module=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['blocking','solve']],type_ignores=[])
    def assertion(message):raise AssertionError(message)
    namespace={'fail':assertion};exec(compile(module,'solver','exec'),namespace)
    policy={'applicants':['a','b'],'slots':[{'id':'x','capacity':1},{'id':'y','capacity':1}]}
    options=lambda ids:[[],[ids[0]],[ids[1]],ids,list(reversed(ids))]
    for lists in itertools.product(options(['x','y']),options(['x','y']),options(['a','b']),options(['a','b'])):
        prefs=dict(zip(['a','b','x','y'],lists))
        result=namespace['solve'](policy,{'profiles':[{'id':key,'tiers':[[item] for item in values],'unknown':[]} for key,values in prefs.items()]})
        stable=[]
        for assignment in itertools.product([None,'x','y'],repeat=2):
            candidate=dict(zip(['a','b'],assignment))
            if any(assignment.count(slot)>1 for slot in ['x','y']):continue
            if any(slot is not None and (slot not in prefs[a] or a not in prefs[slot]) for a,slot in candidate.items()):continue
            blocks=False
            for a in ['a','b']:
                for slot in prefs[a]:
                    if a not in prefs[slot] or candidate[a]==slot:continue
                    current=candidate[a]
                    if current is not None and prefs[a].index(current)<prefs[a].index(slot):continue
                    occupant=next((other for other in ['a','b'] if candidate[other]==slot),None)
                    if occupant is None or prefs[slot].index(a)<prefs[slot].index(occupant):blocks=True
            if not blocks:stable.append(candidate)
        assert result['matching'] in stable
        rank=lambda a,slot:prefs[a].index(slot) if slot is not None else len(prefs[a])+1
        for other in stable:
            assert all(rank(a,result['matching'][a])<=rank(a,other[a]) for a in ['a','b'])
