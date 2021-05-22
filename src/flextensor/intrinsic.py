import tvm

INTRIN_TABLE = {}

target_embedding = {"c -device=micro_dev": 0}



def register_intrin(intrin, override=False):
    key = target_embedding[intrin.target]
    if key not in INTRIN_TABLE:
        INTRIN_TABLE[key] = []
    if intrin in INTRIN_TABLE[key] and not override:
        print("[Warning]: Same intrinsic occurs again %s" % intrin.key) 
    elif intrin in INTRIN_TABLE[key]:
        INTRIN_TABLE[key] = [intrin]
    else:
        INTRIN_TABLE[key].append(intrin)


def get_intrin_table():
    global INTRIN_TABLE
    return INTRIN_TABLE

def reset_intrin(): 
    global INTRIN_TABLE
    INTRIN_TABLE = {}


class Intrinsic(object):
    def __init__(self, category, name, func, args, intrin, target, override=False):
        self.key = "{}_{}_{}".format(category, name, target)
        self.func = func
        self.args = args
        self.intrin = intrin
        self.target = target
        self.category = category
