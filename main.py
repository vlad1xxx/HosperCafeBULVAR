import logging

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler
from settings import CHAT_ID, TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TYPE, CATEGORY, ITEM, QUANTITY, ADDRESS, PHONE, CONFIRMATION, STATUS = range(8)

prices = {
    "капучино": 150,
    "американо": 120,
    "картошка": 200,
    "суп": 250
}

start_markup = ReplyKeyboardMarkup([['Заказать доставку'],
                                    ['Заказать с собой'],
                                    ['Посмотреть меню']], one_time_keyboard=True)

drinks_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton('Капучино', callback_data='ITEM_капучино')],
    [InlineKeyboardButton('Американо', callback_data='ITEM_американо')]
])

menu_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton("Напитки", callback_data='CATEGORY_drinks'),
     InlineKeyboardButton("Горячее", callback_data='CATEGORY_dishes')],
    [InlineKeyboardButton('Удалить позицию', callback_data='CATEGORY_delete')],
    [InlineKeyboardButton('Оформить заказ', callback_data='CATEGORY_arrange')],
])

dishes_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton("Картошка", callback_data='ITEM_картошка')],
    [InlineKeyboardButton("Суп", callback_data='ITEM_суп')],
])

confirm_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton('ПОДТВЕРДИТЬ', callback_data='accept'),
     InlineKeyboardButton('ИЗМЕНИТЬ ДАННЫЕ', callback_data='reject')]
])


async def start(update, context):
    context.user_data.clear()
    context.user_data['order'] = []  # Инициализируем пустой заказ в user_data

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Добро пожаловать\nВыбирайте что хотите",
        reply_markup=start_markup
    )
    return TYPE


async def handle_button_press(update, context):
    category = update.message.text
    context.user_data["category"] = category  # Сохраняем категорию
    if category == 'Заказать доставку':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Выбирайте что хотите заказать',
                                       reply_markup=menu_markup)
    elif category == 'Заказать с собой':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Выбирайте что хотите заказать',
                                       reply_markup=menu_markup)
    elif category == 'Посмотреть меню':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Функция 'Просмотерть меню' в разработке.")
        return TYPE

    return CATEGORY


async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    level, value = data[0], data[1]

    if level == 'CATEGORY':

        if value == 'drinks':
            await query.edit_message_text(text='Выбирайте напиток', reply_markup=drinks_markup)
        elif value == 'dishes':
            await query.edit_message_text(text='Выбирайте горячее', reply_markup=dishes_markup)
        elif value == 'arrange':
            if context.user_data['order']:
                await context.bot.send_message(chat_id=update.effective_chat.id, text='Укажите адрес')
                return ADDRESS
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text='Добавьте что-то в свой заказ')
        elif value == 'delete':  # Обработка нажатия кнопки "Удалить позицию"
            if context.user_data['order']:
                # Создаем кнопки для удаления каждой позиции из заказа
                delete_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f'{item[0].capitalize()} x {item[1]}', callback_data=f'DELETE_{index}')]
                    for index, item in enumerate(context.user_data['order'])
                ])
                await query.edit_message_text(text="Выберите позицию для удаления:", reply_markup=delete_markup)
            else:
                await query.edit_message_text(text="Ваш заказ пуст.")
        return ITEM

    elif level == 'ITEM':
        context.user_data["item"] = value  # Сохраняем выбранный пункт

        await query.edit_message_text(text=f'Вы выбрали {value.capitalize()}. Введите количество.')
        return QUANTITY

    elif level == 'DELETE':
        index_to_remove = int(value)  # Индекс позиции для удаления
        context.user_data['order'].pop(index_to_remove)  # Удаляем позицию по индексу
        # Генерируем новый чек после удаления
        receipt = await create_receipt(context)
        await query.edit_message_text(text='Ваш заказ:\n\n' + receipt, reply_markup=menu_markup)
        return CATEGORY


async def handler_quantity(update, context):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля.")

        # Проверяем, есть ли уже этот товар в заказе
        item_found = False
        for i, (item_name, item_quantity) in enumerate(context.user_data['order']):
            if item_name == context.user_data['item']:
                context.user_data['order'][i] = (item_name, item_quantity + quantity)  # Если товар есть, увеличиваем количество
                item_found = True
                break

        if not item_found:  # Если товара нет в заказе, добавляем новый
            context.user_data['order'].append((context.user_data['item'], quantity))

        # Генерируем новый чек
        receipt = await create_receipt(context)
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Ваш заказ:\n\n' + receipt, reply_markup=menu_markup)
        return CATEGORY

    except ValueError:
        await update.message.reply_text('Пожалуйста, укажите корректное количество (целое число больше 0).')
        return QUANTITY


async def create_receipt(context):
    total = 0
    receipt = ""
    if context.user_data['order']:
        for item in context.user_data['order']:
            item_total = prices[item[0]] * item[1]
            total += item_total
            receipt += f"{item[0].capitalize()} x {item[1]} = {item_total} ₽\n"
        receipt += f"Итого: {total} ₽\n"
    else:
        receipt = "Ваш заказ пуст."
    return receipt


async def handler_address(update, context):
    address = update.message.text
    context.user_data['address'] = address
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Введите свой номер телефона')
    return PHONE


async def handler_phone(update, context):
    phone = update.message.text
    context.user_data['phone'] = phone
    receipt = await create_receipt(context)
    receipt += f'\nАдрес: {context.user_data["address"]}'
    receipt += f'\nНомер телефона: {phone}'
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Ваш заказ:\n\n' + receipt,
                                   reply_markup=confirm_markup)
    return CONFIRMATION


async def handler_confirm(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    receipt = 'Заказ:\n\n' + await create_receipt(context)
    receipt += f'\nАдрес: {context.user_data["address"]}'
    receipt += f'\nНомер телефона: {context.user_data["phone"]}'
    if data == 'accept':
        await context.bot.send_message(chat_id=CHAT_ID, text=receipt)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='ПОДТВЕРЖДЕНО✅')]])
        await query.edit_message_text(text=receipt, reply_markup=reply_markup)
        return STATUS

    else:
        receipt = await create_receipt(context)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=receipt,
                                       reply_markup=menu_markup)
        return CATEGORY


async def handle_status_update(update, context):
    query = update.callback_query
    await query.answer()


async def cancel(update, context):
    context.user_data.clear()


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TYPE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_button_press)],
            CATEGORY: [CallbackQueryHandler(callback_handler)],
            ITEM: [CallbackQueryHandler(callback_handler)],
            QUANTITY: [MessageHandler(filters.TEXT & (~filters.COMMAND), handler_quantity)],
            ADDRESS: [MessageHandler(filters.TEXT & (~filters.COMMAND), handler_address)],
            PHONE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handler_phone)],
            CONFIRMATION: [CallbackQueryHandler(handler_confirm)],
            STATUS: [CallbackQueryHandler(handle_status_update)]
        },
        fallbacks=[MessageHandler(filters.TEXT & (~filters.COMMAND), cancel), CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()
