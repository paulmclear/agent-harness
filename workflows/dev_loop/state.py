from typing import TypedDict


class InputState(TypedDict):
    """Keys accepted by ``graph.invoke``. Everything else is derived by nodes."""

    # control
    debug: bool

    # input data


class State(InputState):
    # derived data

    # output data
    pass
