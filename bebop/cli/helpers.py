import curses

from bebop.models import Post


def render_checkmarks_menu(post: Post):
    todos = post.todos

    def inner(window: curses.window):
        window.keypad(True)
        curses.cbreak()
        curses.noecho()

        position = 0
        while True:
            window.clear()
            window.addstr(f"\n {post.title} - TODO:\n\n", curses.A_UNDERLINE)

            for idx, todo in enumerate(todos):
                selected = ">" if position == idx else " "
                checked = "X" if todo.checked else " "
                window.addstr(f" {selected} [{checked}] {todo.text}\n")

            window.addstr(
                "\n Use Arrows to Move, <Space> for toggle checkmark, <d> for Delete item, "
                "<q> for Save and Exit, <Ctrl-c> to Abort"
            )
            c = window.getch()
            if c == curses.KEY_UP:
                position = (position - 1 + len(todos)) % len(todos)
            if c == curses.KEY_DOWN:
                position = (position + 1) % len(todos)
            if c in (ord(" "), ord("x"), ord("X")):
                todos[position].checked = not todos[position].checked
            if c in (ord("d"), ord("D")):
                todos.remove(todos[position])
                if not len(todos):
                    break
                position = (position - 1 + len(todos)) % len(todos)
            if c in (ord("q"), ord("Q")):
                break

    return inner
