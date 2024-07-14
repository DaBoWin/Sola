# -*- coding: utf-8 -*-
from telegram import Chat, Update, Bot
from telegram.ext import Application, Updater, filters, MessageHandler, CommandHandler, ContextTypes, CallbackContext
from telegram.error import TelegramError
from functools import partial
import asyncio
import random

# 存储抽奖活动的全局变量
active_raffle = None

class Raffle:
    def __init__(self, prize_name, prize_count, secret_code, end_condition):
        self.prize_name = prize_name
        self.prize_count = prize_count
        self.secret_code = secret_code
        self.end_condition = end_condition
        self.participants = []

    def add_participant(self, username):
        if username not in self.participants:
            self.participants.append(username)
            return True
        return False

    def draw_winners(self):
        winners = random.sample(self.participants, min(self.prize_count, len(self.participants)))
        return winners

# 处理 /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '欢迎使用大波小秘抽奖机器人！使用 /create 创建抽奖活动。\n'
        '设置奖品名称、奖品数量、参与口令以及抽奖条件（按时间或参与人数）。'
    )

# 处理 /test 命令
async def test(update: Update,  context: CallbackContext) -> None:
    global active_raffle
    if active_raffle is None:
        await update.message.reply_text(f'没有抽奖')
        return

    chat_id = update.message.chat_id
    winners = active_raffle.draw_winners()
    await update.message.reply_text(
        f'chatid：{chat_id}\n'
        f'获奖者：{", ".join(winners)}\n'
    )
    await context.bot.send_message(
        chat_id if chat_id else context.job.context,
        f'抽奖活动结束！\n'
        f'奖品名称：{active_raffle.prize_name}\n'
        f'获奖者：{", ".join(winners)}\n'
    )
    #active_raffle = None
    await update.message.reply_text(f"测试抽奖")

    

# 检查用户是否为管理员
async def is_user_admin(update: Update) -> bool:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    try:
        chat_member = await update.message.chat.get_member(user_id)
        if chat_member.status in ['administrator', 'creator']:
            return True
    except TelegramError as e:
        print(f"Error checking admin status: {e}")
    return False

# 处理 /create 命令
async def create(update: Update, context: CallbackContext) -> None:
    global active_raffle
    if not is_user_admin(update):
        await update.message.reply_text('只有管理员才能创建抽奖活动。')
        return

    if active_raffle is not None:
        await update.message.reply_text('已有一个进行中的抽奖活动，请结束当前活动后再创建新的活动。')
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            '请使用正确的格式：/create <奖品名称> <奖品数量> <参与口令> <抽奖条件>\n'
            '抽奖条件可以是时间（如 "10m" 表示 10 分钟后抽奖）或人数（如 "10p" 表示 10 人参与后抽奖）。'
        )
        return

    prize_name = args[0]
    prize_count = int(args[1])
    secret_code = args[2]
    end_condition = args[3]

    active_raffle = Raffle(prize_name, prize_count, secret_code, end_condition)
    await update.message.reply_text(
        f'抽奖活动创建成功！\n'
        f'奖品名称：{prize_name}\n'
        f'奖品数量：{prize_count}\n'
        f'参与口令：{secret_code}\n'
        f'抽奖条件：{end_condition}\n'
        '请直接输入 <口令> 参与抽奖。'
    )

    if end_condition.endswith('m'):
        minutes = int(end_condition[:-1])
        context.job_queue.run_once(wrap_draw_raffle(chat_id=update.message.chat_id), minutes * 60)
    elif end_condition.endswith('p'):
        # 不需要额外操作，等待人数到达条件时自动抽奖
        pass
    else:
        await update.message.reply_text('抽奖条件格式错误，请重新创建。')
        active_raffle = None

# 处理 /join 命令
async def join(update: Update, context: CallbackContext) -> None:
    global active_raffle
    if active_raffle is None:
        await update.message.reply_text('当前没有进行中的抽奖活动。')
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text('请使用正确的格式：/join <口令>')
        return

    code = args[0]
    if code != active_raffle.secret_code:
        await update.message.reply_text('口令错误，请重试。')
        return

    user = update.message.from_user
    if user.username is None :
        await update.message.reply_text('请设置用户名称再重试。')
        return
        
    if active_raffle.add_participant(user.username + '-' + str(user.id)):
        length = len(active_raffle.participants)
        await update.message.reply_text(f'{user.username} 已加入抽奖！当前抽奖人数：{length}')
        if active_raffle.end_condition.endswith('p'):
            required_participants = int(active_raffle.end_condition[:-1])
            if len(active_raffle.participants) >= required_participants:
                await draw_raffle(context, update.message.chat_id)
    else:
        await update.message.reply_text(f'{user.username} 已经在抽奖名单中。')

# 处理用户消息
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global active_raffle
    if active_raffle is None:
        return

    text = update.message.text.strip()
    if text != active_raffle.secret_code:
        return

    user = update.message.from_user
    if user.username is None:
        hint_message = await update.message.reply_text('请设置用户名称再重试。')
       # 调度删除消息任务
        context.job_queue.run_once(wrap_delete_message(chat_id=update.message.chat_id, message_id=hint_message.message_id), 30)

        return

    if active_raffle.add_participant(user.username + '-' + str(user.id)):
        length = len(active_raffle.participants)
        participant_message = await update.message.reply_text(f'{user.username} 已加入抽奖！当前抽奖人数：{length}')
        
        # 存储消息 ID 和 chat ID
        context.user_data['participant_message_id'] = participant_message.message_id
        context.user_data['chat_id'] = update.message.chat_id

        # 调度删除消息任务
        context.job_queue.run_once(wrap_delete_message(chat_id=update.message.chat_id, message_id=participant_message.message_id), 30)

        if active_raffle.end_condition.endswith('p'):
            required_participants = int(active_raffle.end_condition[:-1])
            if len(active_raffle.participants) >= required_participants:
                await draw_raffle(context, update.message.chat_id)
    else:
        exit_message = await update.message.reply_text(f'{user.username} 已经在抽奖名单中。')
        # 调度删除消息任务
        context.job_queue.run_once(wrap_delete_message(chat_id=update.message.chat_id, message_id=exit_message.message_id), 30)


async def delete_message(context: CallbackContext) -> None:
    job = context.job
    chat_id = job.data['chat_id']
    message_id = job.data['message_id']
    try:
        await context.bot.delete_message(chat_id, message_id)
    except TelegramError as e:
        print(f"Error deleting message: {e}")

def wrap_delete_message(chat_id, message_id):
    async def wrapped(context: CallbackContext):
        try:
            await context.bot.delete_message(chat_id, message_id)
        except TelegramError as e:
            print(f"Error deleting message: {e}")
    return wrapped


# 处理 /cancel 命令
async def cancel(update: Update, context: CallbackContext) -> None:
    global active_raffle
    if not is_user_admin(update):
        await update.message.reply_text('只有管理员才能取消抽奖活动。')
        return

    if active_raffle is None:
        await update.message.reply_text('当前没有进行中的抽奖活动。')
    else:
        active_raffle = None
        await update.message.reply_text('当前抽奖活动已取消。')

# 抽奖
async def draw_raffle(context: CallbackContext, chat_id: int = None) -> None:
    global active_raffle
    if active_raffle is None:
        return

    winners = active_raffle.draw_winners()
    winners_text = "\n".join([f"@{winner.split('-')[0]}" for winner in winners])
    await context.bot.send_message(
        chat_id if chat_id else context.job.context,
        f'抽奖活动结束！\n'
        f'奖品名称：{active_raffle.prize_name}\n'
        f'获奖者：\n{winners_text}\n'
    )
    active_raffle = None

def wrap_draw_raffle(chat_id):
    async def wrapped(context: CallbackContext):
        await draw_raffle(context, chat_id)
    return wrapped

def main() -> None:
    # 注意这里修改为你的机器人token
    application = Application.builder().token("你的机器人token").build()

    # 注册处理命令的处理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
