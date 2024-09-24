import io
import json
from nbt.nbt import *

with open("1.20.2.json", "r") as f:
    data = json.loads(f.read())

file: NBTFile = NBTFile()


def get_t(o: str):
    t = type(o)

    if t is dict:
        return TAG_Compound
    if t is list:
        return TAG_List
    if t is float:
        return TAG_Float
    if t is int:
        return TAG_Int
    if t is str:
        return TAG_String


def do_dict(d: dict, c: TAG_Compound) -> TAG_Compound:
    for k in d:                                                # foreach key in dict
        v = d[k]                                               # v = value of k in d
        if type(v) is dict:                                    # if type of v is dict
            c.tags.append(do_dict(v, TAG_Compound(name=k)))    # set value of k in c to do_dict(v, TAG_Compound())
        elif type(v) is list:                                  # if type of v is list
            t = get_t(v[0])                                    # get nbt type of first item in list

            li = []
            lit = TAG_List(type=t, name=k, value=li)

            print("List", v)

            for i in v:
                if type(i) is dict:
                    li.append(do_dict(i, TAG_Compound()))
                else:
                    li.append(t(i))

            lit.tags.extend(li)
            c.tags.append(lit)   # set value of k in c to new list tag
        else:
            print(v)
            c.tags.append(get_t(v)(value=v, name=k))

    return c


c = do_dict(data, TAG_Compound())

_io = io.BytesIO()
c._render_buffer(_io)

with open("1.20.2.nbt", "wb") as f1:
    f1.write(bytearray([0x0a]) + _io.getvalue() + bytes(0x00))
