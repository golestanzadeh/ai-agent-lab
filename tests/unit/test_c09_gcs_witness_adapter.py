import json
import pytest
from agent_lab.c09_gcs_witness_adapter import GCSWitnessAdapter
from agent_lab.c09_witness_simulation import WitnessProtocolHarness, WitnessError

class Response:
    def __init__(self, status, payload=None, content=b''):
        self.status_code = status
        self._payload = payload
        self.content = content
    def json(self):
        return self._payload

class Session:
    def __init__(self, payload, upload_status=200, download_status=200):
        self.payload = payload
        self.upload_status = upload_status
        self.download_status = download_status
        self.calls = []
    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if method == 'POST':
            return Response(self.upload_status, {'generation': '123'})
        return Response(self.download_status, content=self.payload)


def test_complete_history_has_no_artificial_page_or_record_ceiling():
    class Pages:
        def request(self,method,path,**kwargs):
            if path.endswith('/o'):
                page=int(kwargs['params'].get('pageToken','0'))
                items=[{'name':f'witness/v1/DEPLOY/{i:020d}','generation':'1'} for i in range(page*100,(page+1)*100)]
                return Response(200,{'items':items,**({'nextPageToken':str(page+1)} if page<101 else {})})
            return Response(200,content=b'controlled record')
    adapter=GCSWitnessAdapter('test',lambda:'writer',lambda:'reader',Pages())
    records=adapter._read_complete_chain_objects('DEPLOY')
    assert len(records)==10200

def fixture():
    h = WitnessProtocolHarness()
    h.execute('OP-1')
    record = h.verify_witness_chain()[-1]
    payload = json.dumps({**record.unsigned(), 'mac': record.mac}, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return h, record, payload

def test_append_uses_generation_zero_and_exact_readback():
    h, record, payload = fixture()
    session = Session(payload)
    adapter = GCSWitnessAdapter('synthetic-test-bucket', lambda: 'writer-token', lambda: 'reader-token', session)
    assert adapter.append(record, h.key) == '123'
    assert session.calls[0][2]['params']['ifGenerationMatch'] == '0'
    assert session.calls[1][2]['params']['generation'] == '123'
    assert session.calls[0][2]['headers']['Authorization'] == 'Bearer writer-token'
    assert session.calls[1][2]['headers']['Authorization'] == 'Bearer reader-token'

def test_append_conflict_fails_closed():
    h, record, payload = fixture()
    with pytest.raises(WitnessError, match='412'):
        GCSWitnessAdapter('test-bucket', lambda: 'writer-token', lambda: 'reader-token', Session(payload, upload_status=412)).append(record, h.key)

def test_readback_mismatch_fails_closed():
    h, record, payload = fixture()
    with pytest.raises(WitnessError, match='mismatch'):
        GCSWitnessAdapter('test-bucket', lambda: 'writer-token', lambda: 'reader-token', Session(payload + b'x')).append(record, h.key)

def test_readback_denied_fails_closed():
    h, record, payload = fixture()
    with pytest.raises(WitnessError, match='403'):
        GCSWitnessAdapter('test-bucket', lambda: 'writer-token', lambda: 'reader-token', Session(payload, download_status=403)).append(record, h.key)

def test_no_credentials_fails_closed():
    h, record, payload = fixture()
    with pytest.raises(WitnessError, match='credentials'):
        GCSWitnessAdapter('test-bucket', lambda: '', lambda: 'reader-token', Session(payload)).append(record, h.key)


def test_r1_g01_chain_read_pins_generations_and_rejects_version_ambiguity():
    h = WitnessProtocolHarness()
    h.execute('OP-1')
    h.execute('OP-2')
    records = h.verify_witness_chain()

    class ChainSession:
        def __init__(self, ambiguous=False):
            self.ambiguous = ambiguous
            self.calls = []

        def request(self, method, path, **kwargs):
            self.calls.append((method, path, kwargs))
            if path.endswith('/o'):
                items = [
                    {'name': records[0].object_key, 'generation': '101', 'size': str(len(records[0].to_bytes()))},
                    {'name': records[1].object_key, 'generation': '102', 'size': str(len(records[1].to_bytes()))},
                ]
                if self.ambiguous:
                    items.append({'name': records[1].object_key, 'generation': '99', 'size': '1'})
                return Response(200, {'items': items})
            generation = kwargs['params']['generation']
            record = records[0] if generation == '101' else records[1]
            return Response(200, content=record.to_bytes())

    session = ChainSession()
    adapter = GCSWitnessAdapter('test-bucket', lambda: 'writer', lambda: 'reader', session)
    observed = adapter.read_chain(h.deployment_id, h.key)
    assert [record.to_bytes() for record in observed] == [record.to_bytes() for record in records]
    assert session.calls[0][2]['params']['versions'] == 'true'
    assert [call[2]['params']['generation'] for call in session.calls[1:]] == ['101', '102']
    assert all(call[2]['headers']['Authorization'] == 'Bearer reader' for call in session.calls)

    with pytest.raises(WitnessError, match='multiple versions'):
        GCSWitnessAdapter(
            'test-bucket', lambda: 'writer', lambda: 'reader', ChainSession(ambiguous=True)
        ).read_chain(h.deployment_id, h.key)


def test_complete_chain_consumes_all_pages_and_accepts_page_order_variation():
    h = WitnessProtocolHarness()
    h.execute('OP-1'); h.execute('OP-2')
    records = h.verify_witness_chain()

    class PagedSession:
        def __init__(self):
            self.calls = []

        def request(self, method, path, **kwargs):
            self.calls.append((method, path, kwargs))
            if path.endswith('/o'):
                token = kwargs['params'].get('pageToken')
                if token is None:
                    return Response(200, {'items': [{'name': records[1].object_key, 'generation': '102'}], 'nextPageToken': 'PAGE-2'})
                assert token == 'PAGE-2'
                return Response(200, {'items': [{'name': records[0].object_key, 'generation': '101'}]})
            generation = kwargs['params']['generation']
            return Response(200, content=records[0].to_bytes() if generation == '101' else records[1].to_bytes())

    session = PagedSession()
    observed = GCSWitnessAdapter('test-bucket', lambda: 'writer', lambda: 'reader', session).read_chain(h.deployment_id, h.key)
    assert observed == tuple(records)
    list_calls = [call for call in session.calls if call[1].endswith('/o')]
    assert len(list_calls) == 2 and list_calls[1][2]['params']['pageToken'] == 'PAGE-2'


@pytest.mark.parametrize('mode', ['repeated-token', 'invalid-token', 'duplicate', 'deleted'])
def test_complete_chain_rejects_pagination_and_version_ambiguity(mode):
    h, record, _ = fixture()

    class BadPagedSession:
        def request(self, method, path, **kwargs):
            if not path.endswith('/o'):
                return Response(200, content=record.to_bytes())
            token = kwargs['params'].get('pageToken')
            item = {'name': record.object_key, 'generation': '101'}
            if mode == 'invalid-token':
                return Response(200, {'items': [item], 'nextPageToken': 7})
            if mode == 'deleted':
                item['timeDeleted'] = '2026-10-23T00:00:00Z'
                return Response(200, {'items': [item]})
            if token is None:
                return Response(200, {'items': [item], 'nextPageToken': 'PAGE-X'})
            if mode == 'repeated-token':
                return Response(200, {'items': [], 'nextPageToken': 'PAGE-X'})
            return Response(200, {'items': [item]})

    with pytest.raises(WitnessError, match='token|multiple versions|deletion'):
        GCSWitnessAdapter('test-bucket', lambda: 'writer', lambda: 'reader', BadPagedSession()).read_chain(h.deployment_id, h.key)
