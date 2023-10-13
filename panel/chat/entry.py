"""The entry module provides a low-level API for rendering chat messages.
"""
from __future__ import annotations

import datetime
import re

from contextlib import ExitStack
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import (
    Any, BinaryIO, ClassVar, Dict, List, Union,
)

import param

from ..io.resources import CDN_DIST
from ..layout import Column, Row
from ..pane.base import panel as _panel
from ..pane.image import (
    PDF, FileBase, Image, ImageBase,
)
from ..pane.markup import HTML, DataFrame, HTMLBasePane
from ..pane.media import Audio, Video
from ..viewable import Viewable
from ..widgets.base import CompositeWidget, Widget
from .icon import ChatCopyIcon, ChatReactionIcons

Avatar = Union[str, BytesIO, ImageBase]
AvatarDict = Dict[str, Avatar]

USER_LOGO = "🧑"
ASSISTANT_LOGO = "🤖"
SYSTEM_LOGO = "⚙️"
ERROR_LOGO = "❌"
GPT_3_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/1024px-ChatGPT_logo.svg.png?20230318122128"
GPT_4_LOGO = "https://upload.wikimedia.org/wikipedia/commons/a/a4/GPT-4.png"
WOLFRAM_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/WolframCorporateLogo.svg/1920px-WolframCorporateLogo.svg.png"

DEFAULT_AVATARS = {
    # User
    "client": USER_LOGO,
    "customer": USER_LOGO,
    "employee": USER_LOGO,
    "human": USER_LOGO,
    "person": USER_LOGO,
    "user": USER_LOGO,
    # Assistant
    "agent": ASSISTANT_LOGO,
    "ai": ASSISTANT_LOGO,
    "assistant": ASSISTANT_LOGO,
    "bot": ASSISTANT_LOGO,
    "chatbot": ASSISTANT_LOGO,
    "machine": ASSISTANT_LOGO,
    "robot": ASSISTANT_LOGO,
    # System
    "system": SYSTEM_LOGO,
    "exception": ERROR_LOGO,
    "error": ERROR_LOGO,
    # Human
    "adult": "🧑",
    "baby": "👶",
    "boy": "👦",
    "child": "🧒",
    "girl": "👧",
    "man": "👨",
    "woman": "👩",
    # Machine
    "chatgpt": GPT_3_LOGO,
    "gpt3": GPT_3_LOGO,
    "gpt4": GPT_4_LOGO,
    "dalle": GPT_4_LOGO,
    "openai": GPT_4_LOGO,
    "huggingface": "🤗",
    "calculator": "🧮",
    "langchain": "🦜",
    "translator": "🌐",
    "wolfram": WOLFRAM_LOGO,
    "wolfram alpha": WOLFRAM_LOGO,
    # Llama
    "llama": "🦙",
    "llama2": "🐪",
}


@dataclass
class _FileInputMessage:
    """
    A dataclass to hold the contents of a file input message.

    Parameters
    ----------
    contents : bytes
        The contents of the file.
    file_name : str
        The name of the file.
    mime_type : str
        The mime type of the file.
    """

    contents: bytes
    file_name: str
    mime_type: str


class ChatEntry(CompositeWidget):
    """
    A widget for displaying chat messages with support for various content types.

    This widget provides a structured view of chat messages, including features like:
    - Displaying user avatars, which can be text, emoji, or images.
    - Showing the user's name.
    - Displaying the message timestamp in a customizable format.
    - Associating reactions with messages and mapping them to icons.
    - Rendering various content types including text, images, audio, video, and more.

    Reference: https://panel.holoviz.org/reference/chat/ChatEntry.html

    :Example:

    >>> ChatEntry(value="Hello world!", user="New User", avatar="😊")
    """

    avatar = param.ClassSelector(
        default="",
        class_=(str, BinaryIO, ImageBase),
        doc="""
        The avatar to use for the user. Can be a single character text, an emoji,
        or anything supported by `pn.pane.Image`. If not set, checks if
        the user is available in the default_avatars mapping; else uses the
        first character of the name.""",
    )

    avatar_lookup = param.Callable(
        default=None,
        doc="""
        A function that can lookup an `avatar` from a user name. The function signature should be
        `(user: str) -> Avatar`. If this is set, `default_avatars` is disregarded.""",
    )

    css_classes = param.List(
        default=["chat-entry"],
        doc="""
        The CSS classes to apply to the widget.""",
    )

    default_avatars = param.Dict(
        default=DEFAULT_AVATARS,
        doc="""
        A default mapping of user names to their corresponding avatars
        to use when the user is specified but the avatar is. You can modify, but not replace the
        dictionary.""",
    )

    reactions = param.List(
        doc="""
        Reactions to associate with the message."""
    )

    reaction_icons = param.ClassSelector(
        class_=(ChatReactionIcons, dict),
        doc="""
        A mapping of reactions to their reaction icons; if not provided
        defaults to `{"favorite": "heart"}`.""",
    )

    timestamp = param.Date(
        doc="""
        Timestamp of the message. Defaults to the creation time."""
    )

    timestamp_format = param.String(default="%H:%M", doc="The timestamp format.")

    show_avatar = param.Boolean(
        default=True, doc="Whether to display the avatar of the user."
    )

    show_user = param.Boolean(
        default=True, doc="Whether to display the name of the user."
    )

    show_timestamp = param.Boolean(
        default=True, doc="Whether to display the timestamp of the message."
    )

    show_reaction_icons = param.Boolean(
        default=True, doc="Whether to display the reaction icons."
    )

    show_copy_icon = param.Boolean(
        default=True, doc="Whether to display the copy icon."
    )

    renderers = param.HookList(
        doc="""
        A callable or list of callables that accept the value and return a
        Panel object to render the value. If a list is provided, will
        attempt to use the first renderer that does not raise an
        exception. If None, will attempt to infer the renderer
        from the value."""
    )

    user = param.Parameter(
        default="User",
        doc="""
        Name of the user who sent the message.""",
    )

    value = param.Parameter(
        doc="""
        The message contents. Can be any Python object that panel can display.""",
        allow_refs=False,
    )

    _value_panel = param.Parameter(doc="The rendered value panel.")

    _stylesheets: ClassVar[List[str]] = [f"{CDN_DIST}css/chat_entry.css"]

    def __init__(self, **params):
        from ..param import ParamMethod  # circular imports

        self._exit_stack = ExitStack()

        self.chat_copy_icon = ChatCopyIcon(
            visible=False, width=15, height=15, css_classes=["copy-icon"]
        )
        if params.get("timestamp") is None:
            params["timestamp"] = datetime.datetime.utcnow()
        if params.get("reaction_icons") is None:
            params["reaction_icons"] = {"favorite": "heart"}
        if isinstance(params["reaction_icons"], dict):
            params["reaction_icons"] = ChatReactionIcons(
                options=params["reaction_icons"], width=15, height=15
            )
        super().__init__(**params)
        self.reaction_icons.link(self, value="reactions", bidirectional=True)
        self.reaction_icons.link(
            self, visible="show_reaction_icons", bidirectional=True
        )
        self.param.trigger("reactions", "show_reaction_icons")
        if not self.avatar:
            self.param.trigger("avatar_lookup")

        render_kwargs = {"inplace": True, "stylesheets": self._stylesheets}
        left_col = Column(
            ParamMethod(self._render_avatar, **render_kwargs),
            max_width=60,
            height=100,
            css_classes=["left"],
            stylesheets=self._stylesheets,
            visible=self.param.show_avatar,
            sizing_mode=None,
        )
        center_row = Row(
            ParamMethod(self._render_value, **render_kwargs),
            self.reaction_icons,
            css_classes=["center"],
            stylesheets=self._stylesheets,
            sizing_mode=None,
        )
        right_col = Column(
            Row(
                ParamMethod(self._render_user, **render_kwargs),
                self.chat_copy_icon,
                stylesheets=self._stylesheets,
                sizing_mode="stretch_width",
            ),
            center_row,
            ParamMethod(self._render_timestamp, **render_kwargs),
            css_classes=["right"],
            stylesheets=self._stylesheets,
            sizing_mode=None,
        )
        self._composite.param.update(
            stylesheets=self._stylesheets, css_classes=self.css_classes
        )
        self._composite[:] = [left_col, right_col]

    @staticmethod
    def _to_alpha_numeric(user: str) -> str:
        """
        Convert the user name to an alpha numeric string,
        removing all non-alphanumeric characters.
        """
        return re.sub(r"\W+", "", user).lower()

    def _avatar_lookup(self, user: str) -> Avatar:
        """
        Lookup the avatar for the user.
        """
        alpha_numeric_key = self._to_alpha_numeric(user)
        # always use the default first
        updated_avatars = DEFAULT_AVATARS.copy()
        # update with the user input
        updated_avatars.update(self.default_avatars)
        # correct the keys to be alpha numeric
        updated_avatars = {
            self._to_alpha_numeric(key): value for key, value in updated_avatars.items()
        }
        # now lookup the avatar
        return updated_avatars.get(alpha_numeric_key, self.avatar)

    def _select_renderer(
        self,
        contents: Any,
        mime_type: str,
    ):
        """
        Determine the renderer to use based on the mime type.
        """
        renderer = _panel
        if mime_type == "application/pdf":
            contents = self._exit_stack.enter_context(BytesIO(contents))
            renderer = partial(PDF, embed=True)
        elif mime_type.startswith("audio/"):
            file = self._exit_stack.enter_context(
                NamedTemporaryFile(suffix=".mp3", delete=False)
            )
            file.write(contents)
            file.seek(0)
            contents = file.name
            renderer = Audio
        elif mime_type.startswith("video/"):
            contents = self._exit_stack.enter_context(BytesIO(contents))
            renderer = Video
        elif mime_type.startswith("image/"):
            contents = self._exit_stack.enter_context(BytesIO(contents))
            renderer = Image
        elif mime_type.endswith("/csv"):
            import pandas as pd

            with BytesIO(contents) as buf:
                contents = pd.read_csv(buf)
            renderer = DataFrame
        elif mime_type.startswith("text"):
            if isinstance(contents, bytes):
                contents = contents.decode("utf-8")
        return contents, renderer

    def _set_default_attrs(self, obj):
        """
        Set the sizing mode and height of the object.
        """
        if hasattr(obj, "objects"):
            obj._stylesheets = self._stylesheets
            for subobj in obj.objects:
                self._set_default_attrs(subobj)
            return None

        is_markup = isinstance(obj, HTMLBasePane) and not isinstance(obj, FileBase)
        if is_markup:
            if len(str(obj.object)) > 0:  # only show a background if there is content
                obj.css_classes = [*obj.css_classes, "message"]
            obj.sizing_mode = None
        else:
            if obj.sizing_mode is None and not obj.width:
                obj.sizing_mode = "stretch_width"

            if obj.height is None:
                obj.height = 500
        return obj

    @staticmethod
    def _is_widget_renderer(renderer):
        return isinstance(renderer, type) and issubclass(renderer, Widget)

    def _create_panel(self, value):
        """
        Create a panel object from the value.
        """
        if isinstance(value, Viewable):
            return value

        renderer = _panel
        if isinstance(value, _FileInputMessage):
            contents = value.contents
            mime_type = value.mime_type
            value, renderer = self._select_renderer(contents, mime_type)
        else:
            try:
                import magic

                mime_type = magic.from_buffer(value, mime=True)
                value, renderer = self._select_renderer(value, mime_type)
            except Exception:
                pass

        renderers = self.renderers.copy() or []
        renderers.append(renderer)
        for renderer in renderers:
            try:
                if self._is_widget_renderer(renderer):
                    value_panel = renderer(value=value)
                else:
                    value_panel = renderer(value)
                if isinstance(value_panel, Viewable):
                    break
            except Exception:
                pass
        else:
            value_panel = _panel(value)

        self._set_default_attrs(value_panel)
        return value_panel

    @param.depends("avatar", "show_avatar")
    def _render_avatar(self) -> HTML | Image:
        """
        Render the avatar pane as some HTML text or Image pane.
        """
        avatar = self.avatar
        if not avatar and self.user:
            avatar = self.user[0]

        if isinstance(avatar, ImageBase):
            avatar_pane = avatar
            avatar_pane.param.update(width=35, height=35)
        elif len(avatar) == 1:
            # single character
            avatar_pane = HTML(avatar)
        else:
            try:
                avatar_pane = Image(avatar, width=35, height=35)
            except ValueError:
                # likely an emoji
                avatar_pane = HTML(avatar)
        avatar_pane.css_classes = ["avatar", *avatar_pane.css_classes]
        avatar_pane.visible = self.show_avatar
        return avatar_pane

    @param.depends("user", "show_user")
    def _render_user(self) -> HTML:
        """
        Render the user pane as some HTML text or Image pane.
        """
        return HTML(self.user, height=20, css_classes=["name"], visible=self.show_user)

    @param.depends("value")
    def _render_value(self) -> Viewable:
        """
        Renders value as a panel object.
        """
        value = self.value
        value_panel = self._create_panel(value)

        # used in ChatFeed to extract its contents
        self._value_panel = value_panel
        return value_panel

    @param.depends("timestamp", "timestamp_format", "show_timestamp")
    def _render_timestamp(self) -> HTML:
        """
        Formats the timestamp and renders it as HTML pane.
        """
        return HTML(
            self.timestamp.strftime(self.timestamp_format),
            css_classes=["timestamp"],
            visible=self.show_timestamp,
        )

    @param.depends("avatar_lookup", "user", watch=True)
    def _update_avatar(self):
        """
        Update the avatar based on the user name.

        We do not use on_init here because if avatar is set,
        we don't want to override the provided avatar.

        However, if the user is updated, we want to update the avatar.
        """
        if self.avatar_lookup:
            self.avatar = self.avatar_lookup(self.user)
        else:
            self.avatar = self._avatar_lookup(self.user)

    @param.depends("_value_panel", watch=True)
    def _update_chat_copy_icon(self):
        value = self._value_panel
        if isinstance(value, HTMLBasePane):
            value = value.object
        if isinstance(value, str) and self.show_copy_icon:
            self.chat_copy_icon.value = value
            self.chat_copy_icon.visible = True
        else:
            self.chat_copy_icon.value = ""
            self.chat_copy_icon.visible = False

    def _cleanup(self, root=None) -> None:
        """
        Cleanup the exit stack.
        """
        if self._exit_stack is not None:
            self._exit_stack.close()
            self._exit_stack = None
        super()._cleanup()

    def stream(self, token: str):
        """
        Updates the entry with the new token traversing the value to
        allow updating nested objects. When traversing a nested Panel
        the last object that supports rendering strings is updated, e.g.
        in a layout of `Column(Markdown(...), Image(...))` the Markdown
        pane is updated.

        Arguments
        ---------
        token: str
          The token to stream to the text pane.
        """
        i = -1
        parent_panel = None
        value_panel = self
        attr = "value"
        value = self.value
        while not isinstance(value, str) or isinstance(value_panel, ImageBase):
            value_panel = value
            if hasattr(value, "objects"):
                parent_panel = value
                attr = "objects"
                value = value.objects[i]
                i = -1
            elif hasattr(value, "object"):
                attr = "object"
                value = value.object
            elif hasattr(value, "value"):
                attr = "value"
                value = value.value
            elif parent_panel is not None:
                value = parent_panel
                parent_panel = None
                i -= 1
        setattr(value_panel, attr, value + token)

    def update(
        self,
        value: dict | ChatEntry | Any,
        user: str | None = None,
        avatar: str | BinaryIO | None = None,
    ):
        """
        Updates the entry with a new value, user and avatar.

        Arguments
        ---------
        value : ChatEntry | dict | Any
            The message contents to send.
        user : str | None
            The user to send as; overrides the message entry's user if provided.
        avatar : str | BinaryIO | None
            The avatar to use; overrides the message entry's avatar if provided.
        """
        updates = {}
        if isinstance(value, dict):
            updates.update(value)
            if user:
                updates["user"] = user
            if avatar:
                updates["avatar"] = avatar
        elif isinstance(value, ChatEntry):
            if user is not None or avatar is not None:
                raise ValueError(
                    "Cannot set user or avatar when explicitly sending "
                    "a ChatEntry. Set them directly on the ChatEntry."
                )
            updates = value.param.values()
        else:
            updates["value"] = value
        self.param.update(**updates)
