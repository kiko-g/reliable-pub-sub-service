fg = lambda text, color: "\33[38;5;" + str(color) + "m" + text + "\33[0m"
bg = lambda text, color: "\33[48;5;" + str(color) + "m" + text + "\33[0m"


class Logger:
    @staticmethod
    def divider(n=30):
        print("-" * n)

    @staticmethod
    def log(message):
        print(fg(message, 8))

    @staticmethod
    def error(message):
        print(fg(message, 1))

    @staticmethod
    def success(message):
        print(fg(message, 2))

    @staticmethod
    def warning(message):
        print(fg(message, 3))

    @staticmethod
    def info(message):
        print(fg(message, 4))

    @staticmethod
    def critical(message):
        print(bg(message, 88))
