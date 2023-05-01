import requests
import grpc
import sys

from ocfl.v1 import index_pb2 as pb2
from ocfl.v1 import index_pb2_grpc as api
from ocflindex.models import Status, Object, ObjectState, ObjectStateChild, ObjectListItem
from typing import Optional

class ObjectListIterator:
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
        return ObjectListItem.from_orm(item)
    
    def __getObjects(self):
        req = pb2.ListObjectsRequest(page_token = self.next_page_token, 
                                    page_size=self.page_size, 
                                    id_prefix=self.prefix)
        resp = self.api.ListObjects(req)
        self.objects = resp.objects
        self.next_page_token = resp.next_page_token

class Client:
    def __init__(self, 
                 srv_addr: str,
                 credentials: Optional[grpc.ChannelCredentials] = grpc.ssl_channel_credentials(), 
                 channel:  Optional[grpc.Channel] = None,
                 insecure: bool = False, 
                 download_base_url: Optional[str] = None) -> None:
        
        self.srv_addr = srv_addr
        self.download_base_url = download_base_url
        if self.download_base_url is None:
            self.download_base_url = self.srv_addr
        if channel is not None:
            self.channel = channel
        elif credentials is not None:
            self.channel = grpc.secure_channel(srv_addr, credentials)
        elif insecure:
            self.channel = grpc.insecure_channel(srv_addr)
        self.api = api.IndexServiceStub(self.channel)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.channel.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        return self.channel.close()

    def get_status(self) -> Status:
        resp = self.api.GetStatus(pb2.GetStatusRequest())
        return Status.from_orm(resp)

    def get_object(self, object_id: str) -> Object:
        obj =  self.api.GetObject(pb2.GetObjectRequest(object_id=object_id))
        print(obj)
        return Object.from_orm(obj)
   
    def get_object_state(self, object_id: str, path: str = ".", version: str = "", recursive: bool = False) -> ObjectState:
        req = pb2.GetObjectStateRequest(
            object_id=object_id,
            base_path = path,
            version = version,
            recursive = recursive,
            page_token="",
            page_size=1)
        resp = self.api.GetObjectState(req)
        next_page_token = resp.next_page_token
        state = ObjectState.from_orm(resp)
        while next_page_token != "":
            req.page_token = next_page_token
            resp = self.api.GetObjectState(req)
            next_page_token = resp.next_page_token
            for ch in resp.children:
                state.children.append(ObjectStateChild.from_orm(ch))
        return state
       
    def list_objects(self, prefix: str ="") -> ObjectListIterator:
        return ObjectListIterator(self.api, prefix=prefix)
    
    def request_digest(self, digest: str):
        resp = requests.get(f"https://{self.srv_addr}/download/{digest}", stream=True)
        for chunk in resp.iter_content(chunk_size=1024 * 64):
           sys.stdout.write(chunk.decode('utf8') + "\n")
        