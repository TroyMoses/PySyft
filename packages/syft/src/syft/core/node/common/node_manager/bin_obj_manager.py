# stdlib
from typing import Iterable
from typing import KeysView
from typing import List
from typing import Optional
from typing import Union
from typing import cast

# third party
import redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from torch import Tensor

# syft absolute
import syft

# relative
from ....common.uid import UID
from ....node.common.node_table.bin_obj_dataset import BinObjDataset
from ....store import ObjectStore
from ....store.storeable_object import StorableObject
from ..node_table.bin_obj_metadata import ObjectMetadata

ENCODING = "UTF-8"


def create_storable(
    _id: UID, data: Tensor, description: str, tags: Optional[List[str]] = None
) -> StorableObject:
    obj = StorableObject(id=_id, data=data, description=description, tags=tags)

    return obj


# class BinObjectManager(ObjectStore):
#     def __init__(self, db: Session) -> None:
#         self.db = db

#     def get_object(self, key: UID) -> Optional[StorableObject]:
#         try:
#             return self.__getitem__(key)
#         except KeyError as e:  # noqa: F841
#             return None

#     def get_objects_of_type(self, obj_type: type) -> Iterable[StorableObject]:
#         return [obj for obj in self.values() if isinstance(obj.data, obj_type)]

#     def __sizeof__(self) -> int:
#         return self.values().__sizeof__()

#     def __str__(self) -> str:
#         return str(self.values())

#     def __len__(self) -> int:
#         local_session = sessionmaker(bind=self.db)()
#         result = local_session.query(ObjectMetadata).count()
#         local_session.close()
#         return result

#     def keys(self) -> KeysView[UID]:
#         local_session = sessionmaker(bind=self.db)()
#         keys = local_session.query(BinObject.id).all()
#         keys = [UID.from_string(k[0]) for k in keys]
#         local_session.close()
#         return keys

#     def values(self) -> List[StorableObject]:
#         obj_keys = self.keys()
#         values = []
#         for key in obj_keys:
#             try:
#                 values.append(self.__getitem__(key))
#             except Exception as e:  # noqa: F841
#                 print("Unable to get item for key", key)  # TODO: TechDebt add logging
#                 print(e)
#         return values

#     def __contains__(self, key: UID) -> bool:
#         local_session = sessionmaker(bind=self.db)()
#         result = (
#             local_session.query(BinObject).filter_by(id=str(key.value)).first()
#             is not None
#         )
#         local_session.close()
#         return result

#     def __getitem__(self, key: UID) -> StorableObject:
#         local_session = sessionmaker(bind=self.db)()
#         bin_obj = local_session.query(BinObject).filter_by(id=str(key.value)).first()
#         obj_metadata = (
#             local_session.query(ObjectMetadata).filter_by(obj=str(key.value)).first()
#         )

#         if not bin_obj or not obj_metadata:
#             raise KeyError(f"Object not found! for UID: {key}")

#         obj = StorableObject(
#             id=UID.from_string(bin_obj.id),
#             data=bin_obj.obj,
#             description=obj_metadata.description,
#             tags=obj_metadata.tags,
#             read_permissions=dict(
#                 syft.deserialize(
#                     bytes.fromhex(obj_metadata.read_permissions), from_bytes=True
#                 )
#             ),
#             search_permissions=dict(
#                 syft.deserialize(
#                     bytes.fromhex(obj_metadata.search_permissions), from_bytes=True
#                 )
#             ),
#             # name=obj_metadata.name,
#         )
#         local_session.close()
#         return obj

#     def is_dataset(self, key: UID) -> bool:
#         local_session = sessionmaker(bind=self.db)()
#         is_dataset_obj = (
#             local_session.query(BinObjDataset).filter_by(obj=str(key.value)).exists()
#         )
#         is_dataset_obj = local_session.query(is_dataset_obj).scalar()
#         local_session.close()
#         return is_dataset_obj

#     def _get_obj_dataset_relation(self, key: UID) -> Optional[BinObjDataset]:
#         local_session = sessionmaker(bind=self.db)()
#         obj_dataset_relation = (
#             local_session.query(BinObjDataset).filter_by(obj=str(key.value)).first()
#         )
#         local_session.close()
#         return obj_dataset_relation

#     def __setitem__(self, key: UID, value: StorableObject) -> None:
#         bin_obj = BinObject(id=str(key.value), obj=value.data)
#         # metadata_dict = storable_to_dict(value)
#         metadata_obj = ObjectMetadata(
#             obj=bin_obj.id,
#             tags=value.tags,
#             description=value.description,
#             read_permissions=cast(
#                 bytes,
#                 syft.serialize(
#                     syft.lib.python.Dict(value.read_permissions), to_bytes=True
#                 ),
#             ).hex(),
#             search_permissions=cast(
#                 bytes,
#                 syft.serialize(
#                     syft.lib.python.Dict(value.search_permissions), to_bytes=True
#                 ),
#             ).hex(),
#             # name=metadata_dict["name"],
#         )

#         obj_dataset_relation = self._get_obj_dataset_relation(key)
#         if obj_dataset_relation:
#             # Create a object dataset relationship for the new object
#             obj_dataset_relation = BinObjDataset(
#                 id=obj_dataset_relation.id,
#                 name=obj_dataset_relation.name,
#                 obj=bin_obj.id,
#                 dataset=obj_dataset_relation.dataset,
#                 dtype=obj_dataset_relation.dtype,
#                 shape=obj_dataset_relation.shape,
#             )

#         if self.__contains__(key):
#             self.delete(key)

#         local_session = sessionmaker(bind=self.db)()
#         local_session.add(bin_obj)
#         local_session.add(metadata_obj)
#         local_session.add(obj_dataset_relation) if obj_dataset_relation else None
#         local_session.commit()
#         local_session.close()

#     def delete(self, key: UID) -> None:
#         try:
#             local_session = sessionmaker(bind=self.db)()

#             object_to_delete = (
#                 local_session.query(BinObject).filter_by(id=str(key.value)).first()
#             )
#             metadata_to_delete = (
#                 local_session.query(ObjectMetadata)
#                 .filter_by(obj=str(key.value))
#                 .first()
#             )
#             local_session.delete(metadata_to_delete)
#             local_session.delete(object_to_delete)
#             local_session.commit()
#             local_session.close()
#         except Exception as e:
#             print(f"{type(self)} Exception in __delitem__ error {key}. {e}")

#     def clear(self) -> None:
#         local_session = sessionmaker(bind=self.db)()
#         local_session.query(BinObject).delete()
#         local_session.query(ObjectMetadata).delete()
#         local_session.commit()
#         local_session.close()

#     def __repr__(self) -> str:
#         return str(self.values())


class RedisStore(ObjectStore):
    def __init__(self, db: Session) -> None:
        self.db = db
        print("connecting to redis")
        self.redis = redis.Redis(host="redis", port=6379)

    def get_object(self, key: UID) -> Optional[StorableObject]:
        try:
            return self.__getitem__(key)
        except KeyError as e:  # noqa: F841
            return None

    def get_objects_of_type(self, obj_type: type) -> Iterable[StorableObject]:
        # raise NotImplementedError("get_objects_of_type")
        # return [obj for obj in self.values() if isinstance(obj.data, obj_type)]
        return self.values()

    def __sizeof__(self) -> int:
        return self.values().__sizeof__()

    def __str__(self) -> str:
        print("RedisStore __str__")

    def __len__(self) -> int:
        return self.client.dbsize()

    def keys(self) -> KeysView[UID]:
        key_bytes = self.redis.keys()
        key_ids = [UID.from_string(str(key.decode("utf-8"))) for key in key_bytes]
        return key_ids

    def values(self) -> List[StorableObject]:
        key_bytes = self.redis.keys()
        # this is bad we need to decouple getting the data from the search
        all_values = []
        for key in key_bytes:
            all_values.append(self.__getitem__(key))

        # return self.redis.mget(self.keys())
        return all_values

    def __contains__(self, key: UID) -> bool:
        return self.redis.contains(str(key.value))

    def __getitem__(self, key: Union[UID, str, bytes]) -> StorableObject:
        try:
            local_session = sessionmaker(bind=self.db)()
            # bin_obj = local_session.query(BinObject).filter_by(id=str(key.value)).first()

            if isinstance(key, UID):
                key_str = str(key.value)
                key_uid = key
            elif isinstance(key, bytes):
                key_str = str(key.decode("utf-8"))
                key_uid = UID.from_string(key_str)
            else:
                key_str = key
                key_uid = UID.from_string(key_str)

            bin = self.redis.get(key_str)
            obj = syft.deserialize(bin, from_bytes=True)
            obj_metadata = (
                local_session.query(ObjectMetadata).filter_by(obj=key_str).first()
            )

            if obj is None or obj_metadata is None:
                raise KeyError(f"Object not found! for UID: {key_uid}")

            obj = StorableObject(
                id=key_uid,
                data=obj,
                description=obj_metadata.description,
                tags=obj_metadata.tags,
                read_permissions=dict(
                    syft.deserialize(
                        bytes.fromhex(obj_metadata.read_permissions), from_bytes=True
                    )
                ),
                search_permissions=dict(
                    syft.deserialize(
                        bytes.fromhex(obj_metadata.search_permissions), from_bytes=True
                    )
                ),
                # name=obj_metadata.name,
            )
            local_session.close()
            return obj
        except Exception as e:
            raise KeyError(f"Object not found! for UID: {key}")

    def is_dataset(self, key: UID) -> bool:
        local_session = sessionmaker(bind=self.db)()
        is_dataset_obj = (
            local_session.query(BinObjDataset).filter_by(obj=str(key.value)).exists()
        )
        is_dataset_obj = local_session.query(is_dataset_obj).scalar()
        local_session.close()
        return is_dataset_obj

    def _get_obj_dataset_relation(self, key: UID) -> Optional[BinObjDataset]:
        local_session = sessionmaker(bind=self.db)()
        obj_dataset_relation = (
            local_session.query(BinObjDataset).filter_by(obj=str(key.value)).first()
        )
        local_session.close()
        return obj_dataset_relation

    def __setitem__(self, key: UID, value: StorableObject) -> None:
        try:
            bin = syft.serialize(value.data, to_bytes=True)
            self.redis.set(str(key.value), bin)
        except Exception as e:
            print("failed to write key to redis", key)

        metadata_obj = ObjectMetadata(
            obj=str(key.value),
            tags=value.tags,
            description=value.description,
            read_permissions=cast(
                bytes,
                syft.serialize(
                    syft.lib.python.Dict(value.read_permissions), to_bytes=True
                ),
            ).hex(),
            search_permissions=cast(
                bytes,
                syft.serialize(
                    syft.lib.python.Dict(value.search_permissions), to_bytes=True
                ),
            ).hex(),
            # name=metadata_dict["name"],
        )

        obj_dataset_relation = self._get_obj_dataset_relation(key)
        if obj_dataset_relation:
            # Create a object dataset relationship for the new object
            obj_dataset_relation = BinObjDataset(
                id=obj_dataset_relation.id,
                name=obj_dataset_relation.name,
                obj=key,
                dataset=obj_dataset_relation.dataset,
                dtype=obj_dataset_relation.dtype,
                shape=obj_dataset_relation.shape,
            )

        local_session = sessionmaker(bind=self.db)()
        local_session.add(metadata_obj)
        local_session.add(obj_dataset_relation) if obj_dataset_relation else None
        local_session.commit()
        local_session.close()

    def delete(self, key: UID) -> None:
        try:
            self.redis.delete(str(key.value))
            local_session = sessionmaker(bind=self.db)()
            metadata_to_delete = (
                local_session.query(ObjectMetadata)
                .filter_by(obj=str(key.value))
                .first()
            )
            local_session.delete(metadata_to_delete)
            local_session.commit()
            local_session.close()
        except Exception as e:
            print(f"{type(self)} Exception in __delitem__ error {key}. {e}")

    def clear(self) -> None:
        self.redis.flushdb()
        local_session = sessionmaker(bind=self.db)()
        local_session.query(ObjectMetadata).delete()
        local_session.commit()
        local_session.close()

    def __repr__(self) -> str:
        return "RedisStore __repr__"
