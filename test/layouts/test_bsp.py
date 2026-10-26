import pytest

import libqtile.config
from libqtile import layout
from libqtile.confreader import Config
from test.helpers import HEIGHT, WIDTH
from test.layouts.layout_utils import assert_focus_path, assert_focused


class BspConfig(Config):
    auto_fullscreen = True
    groups = [
        libqtile.config.Group("a"),
        libqtile.config.Group("b"),
        libqtile.config.Group("c"),
        libqtile.config.Group("d"),
    ]
    layouts = [layout.Bsp(), layout.Bsp(margin_on_single=10), layout.Bsp(wrap_clients=True)]
    floating_layout = libqtile.resources.default_config.floating_layout
    keys = []
    mouse = []
    screens = []
    follow_mouse_focus = False


bsp_config = pytest.mark.parametrize("manager", [BspConfig], indirect=True)

# This currently only tests the window focus cycle


@bsp_config
def test_bsp_window_focus_cycle(manager):
    # setup 3 tiled and two floating clients
    manager.test_window("one")
    manager.test_window("two")
    manager.test_window("float1")
    manager.c.window.toggle_floating()
    manager.test_window("float2")
    manager.c.window.toggle_floating()
    manager.test_window("three")

    # test preconditions, columns adds clients at pos of current, in two stacks
    assert manager.c.layout.info()["clients"] == ["one", "three", "two"]
    # last added window has focus
    assert_focused(manager, "three")

    # assert window focus cycle, according to order in layout
    assert_focus_path(manager, "two", "float1", "float2", "one", "three")


@bsp_config
def test_bsp_margin_on_single(manager):
    manager.test_window("one")

    info = manager.c.window.info()
    assert info["x"] == 0
    assert info["y"] == 0

    manager.c.next_layout()
    info = manager.c.window.info()
    assert info["x"] == 10
    assert info["y"] == 10

    manager.test_window("two")
    # No longer single window so margin reverts to "margin" which is 0
    info = manager.c.window.info()
    assert info["x"] == 0


@bsp_config
def test_bsp_wrap_clients(manager):
    manager.test_window("one")
    manager.test_window("two")

    # Default has no wrapping
    assert_focused(manager, "two")
    manager.c.layout.next()
    assert_focused(manager, "two")
    manager.c.layout.previous()
    assert_focused(manager, "one")
    manager.c.layout.previous()
    assert_focused(manager, "one")

    # Switch to layout with wrapping enabled
    manager.c.next_layout()
    manager.c.next_layout()

    assert_focused(manager, "one")
    manager.c.layout.next()
    assert_focused(manager, "two")
    # Layout should wrap here
    manager.c.layout.next()
    assert_focused(manager, "one")
    # and here
    manager.c.layout.previous()
    assert_focused(manager, "two")


@bsp_config
def test_bsp_border_width_not_doubled(manager):
    """Bsp must apply border_width exactly once per edge.

    When placement was routed through Layout.place_client (which already
    subtracts the border internally), bsp.py still pre-subtracted the
    border itself, shrinking every window by an extra 2 * border_width.
    """
    manager.test_window("one")
    manager.test_window("two")

    border_width = 2  # Bsp's default border_width
    for info in manager.c.windows():
        assert info["width"] == WIDTH - 2 * border_width
        assert info["height"] == HEIGHT // 2 - 2 * border_width


def test_bsp_swap():
    bsp = layout.Bsp()
    bsp._group = libqtile.group._Group("A")

    bsp.add_client("one")
    bsp.add_client("two")
    bsp.add_client("three")
    bsp.add_client("four")

    assert bsp.get_windows() == ["one", "three", "two", "four"]

    bsp.swap("one", "two")

    assert bsp.get_windows() == ["two", "three", "one", "four"]

    bsp.add_client("five")
    bsp.swap("one", "five")

    assert bsp.get_windows() == ["two", "one", "three", "five", "four"]
