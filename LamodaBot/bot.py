import logging

import LamodaBot.bot_settings as settings
from discord.ext import tasks
from discord.ext.commands import Bot, Context
import LamodaBot.utils as utils
import app_logger
from Master.Master import Master
from Master.WebhookHandle import async_send_embed


logger = app_logger.get_logger("common", logging.INFO)

master = Master()
bot = Bot(command_prefix=settings.bot_settings['bot_prefix'])


@bot.command()
async def product(ctx: Context, *, product_tag: str):
    data = await master.async_parse_product_by_tag(product_tag)
    for product in data:
        await ctx.send(embed=product.to_embed())


@bot.command()
async def ping(ctx: Context):
    await ctx.send(content="pong")


@bot.event
async def on_ready():
    logger.info("bot initiated")
    for product_tag in settings.products_to_monitor:
        await utils.process_product(product_tag, master)

    logger.info("bot started parsing products")

    for product in master.product_db:
        await async_send_embed(product.to_embed())
        # DEBUG
        logger.debug(product)

    logger.info("bot parsed all products")


@tasks.loop(seconds=settings.bot_settings['monitor_loop_time'])
async def async_monitor_products():
    # пройти по всем сохраненным элементам и проверить на изменения
    logger.info("bot started monitoring cycle")
    await master.monitor_products()


@tasks.loop(seconds=settings.bot_settings['update_tags_loop_time'])
async def async_monitor_update():
    for product_tag in settings.products_to_monitor:
        await utils.process_product(product_tag, master)

# async_monitor_products.before_loop(bot.wait_until_ready)
# async_monitor_update.before_loop(bot.wait_until_ready)

try:
    async_monitor_products.start()
    async_monitor_update.start()

    bot.run(settings.bot_settings['token'])
except Exception as ex:
    logger.exception(ex)
    # print(ex)
