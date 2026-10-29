"""Private server-to-server Playground integration; front with TLS/rate limiting."""
import os,secrets
from fastapi import FastAPI,Header,HTTPException,Depends
from pydantic import BaseModel,Field
from search import compare

app=FastAPI(title='Playground Startup Graveyard',version='0.1.0',docs_url=None,redoc_url=None,openapi_url=None)
class Idea(BaseModel):
    idea: str=Field(min_length=1,max_length=4000)
    limit: int=Field(default=10,ge=1,le=100)
    country: str|None=Field(default=None,max_length=120)
    industry: str|None=Field(default=None,max_length=200)

def authorize(x_api_key: str|None=Header(default=None)):
    expected=os.environ.get('GRAVEYARD_API_KEY')
    if not expected: raise HTTPException(503,'Service is not configured')
    if not x_api_key or not secrets.compare_digest(x_api_key,expected): raise HTTPException(401,'Unauthorized')

@app.get('/health')
def health(): return {'status':'ok'}

@app.post('/compare',dependencies=[Depends(authorize)])
def compare_idea(body:Idea):
    try: return compare(**body.model_dump())
    except ValueError as e: raise HTTPException(422,str(e)) from e
