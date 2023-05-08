import requests
import grpc
import sys

from ocfl.v1 import index_pb2 as pb2
from ocfl.v1 import index_pb2_grpc as api
from ocflindex.models import Status, Object, ObjectState, ObjectStateChild, ObjectListItem
from typing import Optional, Iterable

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
    def __init__(self, url: str,
                 client_key: Optional[str] = None,
                 client_cert: Optional[str] = None) -> None:
        self.download_base_url = url
        if url.startswith("https://"):
            credentials: grpc.ssl_channel_credentials
            if client_cert is not None and client_key is not None:
                cert = open(client_cert, "rb").read()
                key = open(client_key, "rb").read()
                credentials = grpc.ssl_channel_credentials(private_key=key, certificate_chain=cert)
            else:
                credentials = grpc.ssl_channel_credentials()
            self.srv_addr = url.removeprefix("https://")
            self.channel = grpc.secure_channel(self.srv_addr, credentials=credentials)
        elif url.startswith("http://"):
            self.srv_addr = url.removeprefix("http://")
            self.channel = grpc.insecure_channel(self.srv_addr)
        else:
            raise Exception("client url should begin with 'http://' or 'https://'")
        self.api = api.IndexServiceStub(self.channel)
        self.session = requests.Session()
        self.session.cert = (client_cert, client_key)

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
    
    def content_stream(self, digest: str, **kwargs) -> None:
        """makes a request to download the content with the given digest, returning
        an iterator over the response data. 
        """
        with self.session.get(f"{self.download_base_url}/download/{digest}", stream=True) as r:
            for b in r.iter_content(**kwargs):
                yield b
        