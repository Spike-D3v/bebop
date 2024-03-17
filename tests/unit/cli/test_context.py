import pytest
import typer

from bebop.cli.config import BebopConfig
from bebop.cli.context import BebopContext
from bebop.cli.render import ErrorPanel
from bebop.models import Board, PostGroup, Post
from bebop.token import IndexToken


class TestBebopContext:

    def test_get_tree_by_index_token(self, mocker):
        board = self.get_board(2, 5)
        mocker.patch("bebop.cli.context.BebopContext.load_board", return_value=board)
        config = BebopConfig()
        context = BebopContext(config=config, board_name="test", dry_run=True)
        group, post = context.get_tree_by_index(IndexToken("A5"))
        assert group.title == "PostGroup0"
        assert post.title == "Post0-4"

    def test_fail_get_tree(self, mocker):
        board = self.get_board(1, 1)
        mocker.patch("bebop.cli.context.BebopContext.load_board", return_value=board)
        mocker.patch("rich.console.Console.print")
        config = BebopConfig()
        context = BebopContext(config=config, board_name="test", dry_run=True)
        token = IndexToken("A5")
        with pytest.raises(typer.Abort):
            context.get_tree_by_index(token)
        panel = ErrorPanel(data=f"The Token '{token}' does not exists")
        context.console.print.assert_called_once_with(panel)

    @staticmethod
    def get_board(groups=1, posts=1) -> Board:
        board_posts = []
        for i in range(groups):
            group_posts = []
            for j in range(posts):
                post = Post(title=f"Post{i}-{j}")
                group_posts.append(post)
            group = PostGroup(title=f"PostGroup{i}", posts=group_posts)
            board_posts.append(group)
        return Board(title="Test", posts=board_posts, name="test")
