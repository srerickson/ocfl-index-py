from pydantic import BaseModel
from pydantic.utils import GetterDict
from datetime import datetime
from typing import Any, Optional

class Status(BaseModel):
    """ Response from GetStatus call
    """
    status: str
    store_root_path: str
    store_spec: str
    store_description: str
    num_object_paths: int
    num_inventories: int
    class Config:
        orm_mode = True

class VersionUser(BaseModel):
    """User info in an ObjectVersion
    """
    name: str
    address: str
    class Config:
        orm_mode = True

class ObjectVersionGetter(GetterDict):
    """Used to customize ObjectVersion.from_orm
    """
    def get(self, key: str, default: Any) -> Any:
        if key == "created":
            # convert the created timestamp to datetime
            return self._obj.created.ToDatetime()
        return super().get(key, default)

class ObjectVersion(BaseModel):
    """Version information in an Object"""
    num: str
    user: VersionUser
    message: str
    created: datetime
    class Config:
        orm_mode = True
        getter_dict = ObjectVersionGetter 

class ObjectGetter(GetterDict):
    """Used to customize Object.from_orm
    """
    def get(self, key: str, default: Any) -> Any:
        # used to convert 
        if key == "versions":
            versions: list[ObjectVersion] = []
            for v in self._obj.versions:
                versions.append(ObjectVersion.from_orm(v))
            return versions
        
        return super().get(key, default)

class Object(BaseModel):
    """Basic information about a specific OCFL Object
    """
    object_id: str
    spec: str
    root_path: str
    digest_algorithm: str
    versions: list[ObjectVersion]
    class Config:
        orm_mode = True
        getter_dict = ObjectGetter

class ObjectStateChildGetter(GetterDict):
    """Used to customize ObjectState.from_orm
    """
    def get(self, key: str, default: Any) -> Any:
        return super().get(key, default)

class ObjectStateChild(BaseModel):
    name: str
    digest: str
    isdir: bool = False
    size: Optional[int] = None
    class Config:
        orm_mode = True
        getter_dict = ObjectStateChildGetter

class ObjectStateGetter(GetterDict):
    """Used to customize ObjectState.from_orm
    """
    def get(self, key: str, default: Any) -> Any:
        if key == "children":
            children: list[ObjectStateChild] = []
            for ch in self._obj.children:
                children.append(ObjectStateChild.from_orm(ch))
            return children
        return super().get(key, default)

class ObjectState(BaseModel):
    digest: str
    name: str = "."
    isdir: bool = False
    size: Optional[int] = None
    children: Optional[list[ObjectStateChild]] = None
    class Config:
        orm_mode = True
        getter_dict = ObjectStateGetter

class ObjectListItemGetter(GetterDict):
    """Used to customize ObjectListItem.from_orm
    """
    def get(self, key: str, default: Any) -> Any:
        if key == "v1_created":
            return self._obj.v1_created.ToDatetime()
        if key == "head_created":
            return self._obj.head_created.ToDatetime()
        return super().get(key, default)    

class ObjectListItem(BaseModel):
    object_id: str
    head: str
    v1_created: datetime
    head_created: datetime
    class Config:
        orm_mode = True
        getter_dict = ObjectListItemGetter
