from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Representa los campos básicos"""

    model_config = ConfigDict(alias_generator=to_camel)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)
    author: Optional[str] = Field(default=None)


class Comment(BaseSchema):
    """Representa un comentario"""

    text: str


class Todo(BaseSchema):
    """Representa una tarea"""

    text: str
    checked: bool = Field(default=False)


class BebopElement(BaseSchema):
    """Representa un elemento de bebop"""

    title: str
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    description_file: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=lambda: [])
    comments: List[Comment] = Field(default_factory=lambda: [])


class Post(BebopElement):
    """Representa un post"""

    archived: bool = Field(default=False)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    todos: List[Todo] = Field(default_factory=lambda: [])

    @property
    def checked_todos(self) -> List[Todo]:
        return [x for x in self.todos if x.checked]

    @property
    def todo_progress(self) -> int:
        if not len(self.todos):
            return 0
        return round(len(self.checked_todos) * 100 / len(self.todos))

    def __repr__(self):
        return f"<Post: {self.title}>"


class PostGroup(BebopElement):
    """Representa un grupo de posts"""

    archived: bool = Field(default=False)
    posts: List[Post] = Field(default_factory=lambda: [])

    @property
    def active_posts(self) -> List[Post]:
        return [x for x in self.posts if not x.archived]

    def __repr__(self):
        return f"<PostGroup: {self.title}>"


class Board(BebopElement):
    """Representa un tablero kanban"""

    posts: List[PostGroup] = Field(default_factory=lambda: [])

    @property
    def active_posts(self) -> List[PostGroup]:
        return [x for x in self.posts if not x.archived]
