import json
import pytest
from agent_lab.gemini_document_extraction import _parse_result

def valid():return {'document_type':'INVOICE','tax_category':'CANDIDATE','issuer':None,'document_date':None,'tax_year':2025,'fields':[{'name':'amount','value':'1.00','page':1,'evidence':'1,00 EUR','confidence':.8}],'confidence':.8,'needs_human_review':True,'notes':[]}
def test_valid_closed_extraction_without_optional_dependencies():assert _parse_result(json.dumps(valid())).fields[0].page==1
@pytest.mark.parametrize('change',[{'extra':1},{'confidence':True},{'fields':[]},{'tax_year':True},{'notes':'wrong'},{'needs_human_review':'false'}])
def test_invalid_provider_schema(change):
    p=valid();p.update(change)
    with pytest.raises(ValueError):_parse_result(json.dumps(p))
@pytest.mark.parametrize('change',[{'page':None},{'page':True},{'page':0},{'evidence':''},{'value':1},{'confidence':float('nan')},{'extra':0}])
def test_invalid_field(change):
    p=valid();p['fields'][0].update(change)
    with pytest.raises(ValueError):_parse_result(json.dumps(p))
def test_duplicate_provider_keys_rejected():
    s=json.dumps(valid()).replace('"issuer": null','"issuer": null,"issuer":null')
    with pytest.raises(ValueError):_parse_result(s)
