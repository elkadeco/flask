import os,tempfile,importlib
def getapp():
    fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd); os.environ['AMALORA_DB_PATH']=path
    import app as m; importlib.reload(m); m.app.config['TESTING']=True; return m.app,path
def test_health():
    app,path=getapp()
    with app.test_client() as c: assert c.get('/health').json['ok']
    os.unlink(path)
def test_booking_conflict():
    app,path=getapp()
    with app.test_client() as c:
        p=c.get('/api/patients').json; d=c.get('/api/clinicians').json
        x={'patient_id':p[0]['id'],'clinician_id':d[0]['id'],'service':'Test','resource':'Room X','start_at':'2030-01-01T10:00:00+00:00','duration_minutes':60,'status':'confirmed'}
        assert c.post('/api/appointments',json=x).status_code==201
        x['patient_id']=p[1]['id']; assert c.post('/api/appointments',json=x).status_code==409
    os.unlink(path)
def test_scribe_is_draft():
    app,path=getapp()
    with app.test_client() as c:
        r=c.post('/api/ai/scribe',json={'transcript':'Patient reports dry skin.'})
        assert r.json['status']=='draft_requires_clinician_review'
        assert r.json['coding_suggestions']==[]
    os.unlink(path)
