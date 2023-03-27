import grpc
import ocfl.v1.index_pb2_grpc as api
import ocfl.v1.index_pb2 as pb2


class Client:
    def __init__(self, channel):
        self.api = api.IndexServiceStub(channel)

    def get_status(self):
        return self.api.GetStatus(pb2.GetStatusRequest())

    def get_object(self, id):
        return self.api.GetObject(pb2.GetObjectRequest(object_id=id))
    
    def list_objects(self, prefix=""):
        return ListObjectsPager(self.api, prefix=prefix)

class ListObjectsPager:

    def __init__(self, api, page_size=11, prefix=""):
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
        return item
    
    def __getObjects(self):
        # string page_token = 1;
        # int32 page_size = 2;
        # string id_prefix = 3;
        req = pb2.ListObjectsRequest(page_token = self.next_page_token, 
                                    page_size=self.page_size, 
                                    id_prefix=self.prefix)
        resp = self.api.ListObjects(req)
        self.objects = resp.objects
        self.next_page_token = resp.next_page_token