"""Named maps and start/goal pairs shared by tests and notebooks."""

from lib import maps


def grid_open():
    g = maps.grid_open()
    return g, (0, 0), (7, 7)


def grid_wall():
    g = maps.grid_wall()
    return g, (0, 0), (7, 7)


def grid_maze():
    g = maps.grid_maze()
    return g, (0, 0), (7, 7)


def topo_oneway():
    g = maps.topo_oneway()
    return g, "I0", "G1"


def corridor_headon():
    g = maps.corridor_headon()
    return g, "A", "B"


def two_agent_tunnel():
    """Two agents on separate rows of an open grid — prioritized planning is easy."""
    g = maps.grid_open(6, 4)
    starts = {"a": (0, 0), "b": (0, 3)}
    goals = {"a": (5, 0), "b": (5, 3)}
    return g, starts, goals


def two_agent_swap():
    g = maps.cbs_cardinal_map()
    starts = {"a": (0, 1), "b": (4, 1)}
    goals = {"a": (4, 1), "b": (0, 1)}
    return g, starts, goals


def assign_pair():
    g = maps.assign_cross_map()
    robots = ["r0", "r1"]
    starts = {"r0": "R0", "r1": "R1"}
    tasks = ["G0", "G1"]
    return g, robots, starts, tasks
