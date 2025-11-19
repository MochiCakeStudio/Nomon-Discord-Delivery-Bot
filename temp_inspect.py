import sys
sys.path.append('..')
from cogs.embed_cog import EmbedCog

# Create a mock bot instance for inspection
class MockBot:
    pass

bot = MockBot()
cog = EmbedCog(bot)

cmd = cog.slash_embed
check_func = cmd.checks[0]
print('Closure vars:', check_func.__closure__)
if check_func.__closure__:
    print('Closure 0:', check_func.__closure__[0].cell_contents)
