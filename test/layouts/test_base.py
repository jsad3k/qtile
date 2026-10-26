import pytest

import libqtile
from libqtile.command.base import expose_command
from libqtile.confreader import Config
from libqtile.layout.base import _SimpleLayoutBase
from test.helpers import WIDTH


class DummyLayout(_SimpleLayoutBase):
    defaults = [
        ("current_offset", 0, ""),
        ("current_position", None, ""),
    ]

    def __init__(self, **config):
        _SimpleLayoutBase.__init__(self, **config)
        self.add_defaults(DummyLayout.defaults)

    def add_client(self, client):
        return super().add_client(
            client, offset_to_current=self.current_offset, client_position=self.current_position
        )

    def configure(self, client, screen_rect):
        pass

    @expose_command("up")
    def previous(self):
        _SimpleLayoutBase.previous()

    @expose_command("down")
    def next(self):
        _SimpleLayoutBase.next()


class BaseLayoutConfigBottom(Config):
    auto_fullscreen = True
    groups = [libqtile.config.Group("a")]
    layouts = [DummyLayout(current_position="bottom")]
    floating_layout = libqtile.resources.default_config.floating_layout
    keys = []
    mouse = []
    screens = []


class BaseLayoutConfigTop(Config):
    auto_fullscreen = True
    groups = [libqtile.config.Group("a")]
    layouts = [DummyLayout(current_position="top")]
    floating_layout = libqtile.resources.default_config.floating_layout
    keys = []
    mouse = []
    screens = []


baselayoutconfigbottom = pytest.mark.parametrize(
    "manager", [BaseLayoutConfigBottom], indirect=True
)
baselayoutconfigtop = pytest.mark.parametrize("manager", [BaseLayoutConfigTop], indirect=True)


@baselayoutconfigbottom
def test_base_client_position_bottom(manager):
    manager.test_window("one")
    manager.test_window("two")
    assert manager.c.layout.info()["clients"] == ["one", "two"]


@baselayoutconfigtop
def test_base_client_position_top(manager):
    manager.test_window("one")
    manager.test_window("two")
    assert manager.c.layout.info()["clients"] == ["two", "one"]


class TwoSlotLayout(_SimpleLayoutBase):
    """Minimal side-by-side layout used to exercise Layout.place_client in
    isolation from any specific layout's column/stack bookkeeping. The first
    client always occupies the left half of the screen, the second client
    the right half."""

    defaults = [
        ("border_width", 0, ""),
        ("margin", 0, ""),
    ]

    def __init__(self, **config):
        _SimpleLayoutBase.__init__(self, **config)
        self.add_defaults(TwoSlotLayout.defaults)

    def configure(self, client, screen_rect):
        index = self.clients.index(client)
        slot_width = screen_rect.width // 2
        left = screen_rect.x + index * slot_width
        self.place_client(
            client,
            screen_rect,
            left,
            screen_rect.y,
            slot_width,
            screen_rect.height,
            self.border_width,
            None,
            margin=self.margin,
        )
        client.unhide()


class TwoSlotLayoutConfig(Config):
    auto_fullscreen = True
    groups = [libqtile.config.Group("a")]
    # N, E, S, W margins are all different so each can be identified individually.
    layouts = [TwoSlotLayout(margin=[2, 4, 8, 16])]
    floating_layout = libqtile.resources.default_config.floating_layout
    keys = []
    mouse = []
    screens = []


two_slot_layout_config = pytest.mark.parametrize("manager", [TwoSlotLayoutConfig], indirect=True)


@two_slot_layout_config
def test_place_client_no_double_margin(manager):
    """Layout.place_client must suppress the east margin on a window that
    isn't the rightmost one, so adjacent windows don't end up with a
    doubled-up gap between them."""
    manager.test_window("one")
    manager.test_window("two")

    # New clients are inserted at the head of the client list by default, so
    # identify the left/right slots by position rather than by add order.
    left, right = sorted(manager.c.windows(), key=lambda w: w["x"])

    # West/north margins are always applied (they provide the inter-window
    # gap); east/south are only applied at the true screen edge. So the gap
    # between the two windows must equal the west margin (16) applied once by
    # the right one -- not doubled with the left one's east margin, which
    # must be suppressed since it isn't the rightmost window.
    assert right["x"] - (left["x"] + left["width"]) == 16

    # The left window still gets its west margin against the screen's left
    # edge, and the right window (the rightmost one) still gets its east
    # margin against the screen's right edge.
    assert left["x"] == 16
    assert right["x"] + right["width"] == WIDTH - 4
