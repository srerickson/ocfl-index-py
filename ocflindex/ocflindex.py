import ocfl.v1.index_pb2_grpc as api
import ocfl.v1.index_pb2 as pb2
import requests
import grpc
import sys
from dataclasses import dataclass
from datetime import datetime


class Client:
    def __init__(self, srv_addr, tls = True, credentials = None, channel=None):
        self.srv_addr = srv_addr
        if channel is not None:
            self.channel = channel
        elif credentials is not None:
            self.channel = grpc.secure_channel(srv_addr, credentials)
        elif tls:
            self.channel = grpc.secure_channel(srv_addr, grpc.ssl_channel_credentials())
        else:
            self.channel = grpc.insecure_channel(srv_addr)
        self.api = api.IndexServiceStub(self.channel)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.channel.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        return self.channel.close()

    def get_status(self):
        return self.api.GetStatus(pb2.GetStatusRequest())

    def get_object(self, object_id):
        obj =  self.api.GetObject(pb2.GetObjectRequest(object_id=object_id))
        versions = []
        for v in obj.versions:
            # todo check if user exists
            v = ObjectVersion(
                user_name = v.user.name,
                user_addr = v.user.address,
                num = v.num,
                message = v.message,
                created = v.created.ToDatetime())
            versions.append(v)
        return Object(
            object_id  = obj.object_id,
            spec = obj.spec,
            root_path = obj.root_path,
            digest_algorithm = obj.digest_algorithm,
            versions = versions,
        )
   
    def get_object_state(self, object_id, path=".", version="", recursive=False):
        req = pb2.GetObjectStateRequest(
            object_id=object_id,
            base_path = path,
            version = version,
            recursive = recursive,
            page_token="",
            page_size=1)
        resp = self.api.GetObjectState(req)
        next_page_token = resp.next_page_token
        state = ObjectState.FromResponse(resp)
        while next_page_token != "":
            req.page_token = next_page_token
            resp = self.api.GetObjectState(req)
            next_page_token = resp.next_page_token
            for ch in resp.children:
                state.children.append(ObjectStateItem.FromResponse(ch))
        return state
       
    def list_objects(self, prefix=""):
        return ObjectList(self.api, prefix=prefix)
    

    def request_digest(self, digest):
        resp = requests.get(f"https://{self.srv_addr}/download/{digest}", stream=True)
        for chunk in resp.iter_content(chunk_size=1024 * 64):
           sys.stdout.write(chunk.decode('utf8') + "\n")
        
        

    

@dataclass
class ObjectVersion:
    user_name: str
    user_addr: str
    num: str
    message: str
    created: datetime

@dataclass
class Object:
    object_id: str
    spec: str
    root_path: str
    digest_algorithm: str
    versions: list[ObjectVersion]
    

@dataclass
class ObjectStateItem:
    name: str
    digest: str
    isdir: bool = False
    size: int = None

    @classmethod
    def FromResponse(cls, resp):
        return cls(
            name = resp.name,
            digest = resp.digest,
            isdir = resp.isdir,
            size = _handle_size(resp.size, resp.has_size))
       

@dataclass
class ObjectState:
    digest: str
    isdir: bool = False
    size: int = 0
    children: list[ObjectStateItem] = None

    @classmethod
    def FromResponse(cls, resp):
        state = cls(
            isdir = resp.isdir,
            size = _handle_size(resp.size, resp.has_size),
            digest= resp.digest)
        if resp.isdir:
            state.children = []
        for ch in resp.children:
            state.children.append(ObjectStateItem.FromResponse(ch))
        return state

@dataclass
class ObjectListItem:
    object_id: str
    head: str
    v1_created: datetime
    head_created: datetime

class ObjectList:
    def __init__(self, api, page_size=1000, prefix=""):
        self.api = api
        self.next_page_token = ""
        self.page_size=page_size
        self.prefix=prefix
        self.offset=0
        self.objects=[]
        self.__getObjects()

    def __iter__(self):
        return self
    
    def __next__(self):
        if self.offset >= len(self.objects) and self.next_page_token != "":
                self.offset = 0
                self.__getObjects()
        if self.offset >= len(self.objects):
            raise StopIteration
        item = self.objects[self.offset]
        self.offset += 1
        return ObjectListItem(
            object_id = item.object_id,
            head = item.head,
            v1_created = item.v1_created.ToDatetime(),
            head_created = item.head_created.ToDatetime(),
        )
    
    def __getObjects(self):
        req = pb2.ListObjectsRequest(page_token = self.next_page_token, 
                                    page_size=self.page_size, 
                                    id_prefix=self.prefix)
        resp = self.api.ListObjects(req)
        self.objects = resp.objects
        self.next_page_token = resp.next_page_token


def _handle_size(size, has_size):
    s = None
    if has_size:
        s = size
    return s