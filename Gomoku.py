import asyncio
import platform
from ui import GomokuGame

FPS = 60

def setup():
    global game
    game = GomokuGame()

async def main():
    setup()
    while True:
        game.update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())