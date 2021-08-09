from bot import bot_main

import foodgetter

def main() -> None:
    # Start bot
    foodgetter.load_foods()
    bot_main()

if __name__ == '__main__':
    main()