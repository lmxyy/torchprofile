import warnings

import torch
import torch.jit

from .ir import Variable, Node, Graph
from .utils import Flatten

__all__ = ['trace']


def trace(model, *args, **kwargs):
    assert not kwargs, 'Keyword arguments are not supported for now. ' \
                       'Please use positional arguments instead!'

    with warnings.catch_warnings(record=True):
        trace, _ = torch.jit.get_trace_graph(Flatten(model), tuple(args), kwargs=kwargs)

    variables = dict()
    for node in trace.graph().nodes():
        for var in list(node.inputs()) + list(node.outputs()):
            if 'tensor' in var.type().kind().lower():
                dtype = var.type().scalarType()
                shape = var.type().sizes()
            else:
                dtype = str(var.type())
                shape = None
            variables[var] = Variable(name=var.debugName(), dtype=dtype, shape=shape)

    nodes = []
    for node in trace.graph().nodes():
        attributes = {name: getattr(node, node.kindOf(name))(name) for name in node.attributeNames()}
        inputs = [variables[var] for var in node.inputs()]
        outputs = [variables[var] for var in node.outputs()]
        scope = node.scopeName().replace('Flatten/', '', 1).replace('Flatten', '', 1)
        nodes.append(Node(operator=node.kind(), attributes=attributes, inputs=inputs, outputs=outputs, scope=scope))

    inputs = [variables[var] for var in trace.graph().inputs()]
    outputs = [variables[var] for var in trace.graph().outputs()]
    return Graph(variables=list(variables.values()), inputs=inputs, outputs=outputs, nodes=nodes)
