FIXME: PROPER README

File format for .ini file:

GRAPH_1 : {graph_1_var_1, graph_1_var_2, graph_1_var_3, ... }

GRAPH_2 : {graph_2_var_1, graph_2_var_2, graph_2_var_3, ...}

.
.
.

GRAPH_N : {graph_n_ ... }


09/01/25:
Important limitation - the parser currently assumes that only 3-element Array and Value objects are being used. This is a serious limitation, and will break if you try to log other types of data. This will be fixed in the next push, whenever that is... @duffleBagDoggo on discord for deets.
