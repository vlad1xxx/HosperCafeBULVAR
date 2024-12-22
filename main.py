import logging

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler
from settings import CHAT_ID, TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TYPE, CATEGORY, ITEM, QUANTITY, ADDRESS, PHONE, CONFIRMATION, STATUS = range(8)

prices = {
    'Закуски': {
        'Баклажаны Тянива': 450,
        'Креветки в кляре': 830,
        'Куриные крылышки': 650,
        'Мясная тарелка': 700,
        'Сырная тарелка': 630,
        'Сырные палочки': 580,
        'Тарелки к Пиву': 1550,
        'Чесночные гренки': 250
    },
    'Салаты': {
        'Зеленый салат': 400,
        'Овощной': 380,
        'Салат с Киноа': 500,
        'Стейк салат': 550,
        'Цезарь с Креветками': 550,
        'Цезарь с Курицей': 450
    },
    'Супы': {
        'Куриный суп': 350,
        'Борщ': 450,
        'Том Ям': 750
    },
    'Паста': {
        'Карбонара': 530,
        'Пенне Болоньезе': 450,
        'Феттучини Ветчина Грибы': 480
    },
    'Гарниры': {
        'Картофель Мини': 150,
        'Овощи Гриль': 150,
        'Пюре': 150,
        'Рис с овощами': 150,
        'Фри': 150,
        'Овощное соте': 150
    },
    'Хоспер': {
        'Бургер с говядиной': 690,
        'Бургер с курицей': 650,
        'Бургер Сицилийский': 700,
        'Говяжьи Щечки': 700,
        'Купаты': 500,
        'Свиные ребра': 750,
        'Цыпленок': 850,
        'Вырезка': 1500,
        'Рибай': 1250,
        'Шашлык из Индейки': 650,
        'Шашлык Куриный': 600,
        'Шашлык Свиной': 650,
        'ХосперСет': 3700
    },
    'Римская пицца': {
        'Маргарита': 500,
        'Мясная': 750,
        'Пепперони': 550,
        'Фокачча': 280,
        'Четыре Сыра': 630
    },
    'Десерты': {
        'Брауни': 450,
        'Мороженое шарик': 100,
        'Тирамису': 450,
        'Чизкейк': 450,
        'Яблочный Криспи': 400,
        'Клубничный топпинг': 150,
        'Лимонный топпинг': 150,
        'Шоколадный топпинг': 150
    },
    'Соус': {
        'Аджика': 100,
        'Барбекю': 100,
        'Блю чиз': 100,
        'Горчичный': 100,
        'Перечный': 100,
        'Сырный': 100,
        'Чесночный': 100,
    },
    'Кофе': {
        'Американо 180мл': 150,
        'Американо 300мл': 200,
        'Капучино 200мл': 180,
        'Капучино 300мл': 230,
        'Латте 200мл': 200,
        'Латте 300мл': 250,
        'Раф 200мл': 300,
        'Раф 300мл': 350,
        'Флэт Уайт 150мл': 200,
        'Эспрессо 30мл': 150
    },
    'Кофе Альтернативный': {
        'Капучинно 200мл': 260,
        'Капучинно 300мл': 330,
        'Латте 200мл': 280,
        'Латте 300мл': 350,
        'Флэт Уайт 150мл': 280
    },
    'Лимонады': {
        'Ананас Карамель Мята 400мл': 250,
        'Ананас Карамель Мята 1,5л': 800,
        'Груша Имбирь Бузина 400мл': 250,
        'Груша Имбирь Бузина 1,5л': 800,
        'Манго Каламанси 400мл': 250,
        'Манго Каламанси 1,5л': 800,
        'Манго Маракуйя 400мл': 250,
        'Манго Маракуйя 1,5л': 800,
        'Мохито 400мл': 250,
        'Мохито 1,5л': 800,
        'Мохито Клубничный 400мл': 250,
        'Мохито Клубничный 1,5л': 800,
    }
}

start_markup = ReplyKeyboardMarkup([
    ['Заказать доставку'],
    ['Заказать с собой'],
    ['Посмотреть меню']
], one_time_keyboard=True)

menu_buttons = [
    [InlineKeyboardButton(category, callback_data=f"CATEGORY_{category}") for category in list(prices.keys())[i:i + 2]]
    for i in range(0, len(prices.keys()), 2)
]

menu_buttons.append([InlineKeyboardButton('Удалить позицию', callback_data='CATEGORY_delete')])
menu_buttons.append([InlineKeyboardButton('Оформить заказ', callback_data='CATEGORY_arrange')])
menu_markup = InlineKeyboardMarkup(menu_buttons)


async def start(update, context):
    context.user_data.clear()
    context.user_data['order'] = []

    await update.message.reply_text(
        "Добро пожаловать! Выберите, что хотите.",
        reply_markup=start_markup
    )
    return TYPE


async def handle_button_press(update, context):
    context.user_data['order'] = []
    type_order = update.message.text
    context.user_data['type'] = type_order

    if type_order in ['Заказать доставку', 'Заказать с собой']:
        await update.message.reply_text(
            'Выберите категорию:',
            reply_markup=menu_markup
        )
    elif type_order == 'Посмотреть меню':
        await update.message.reply_text("Функция 'Посмотреть меню' в разработке.")
        return TYPE

    return CATEGORY


async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    level, value = data[0], '_'.join(data[1:])

    if level == 'CATEGORY':
        if value in prices:
            items = list(prices[value].items())
            buttons = [
                [InlineKeyboardButton(f"{item} ({price} ₽)", callback_data=f"ITEM_{item}") for item, price in
                 items[i:i + 2]]
                for i in range(0, len(items), 2)
            ]
            markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(
                text=f"Выберите блюдо из категории '{value}':",
                reply_markup=markup
            )
            return ITEM
        elif value == 'delete':
            pass
        elif value == 'arrange':
            if context.user_data['order']:
                await context.bot.send_message(chat_id=update.effective_chat.id, text='Укажите адрес')
                return ADDRESS
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text='Добавьте что-то в свой заказ')
        return ITEM
    elif level == 'ITEM':
        context.user_data['item'] = value
        await query.edit_message_text(
            text=f"Вы выбрали '{value}'. Введите количество:"
        )
        return QUANTITY


async def handle_quantity(update, context):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля.")

        item_name = context.user_data['item']
        order = context.user_data['order']

        for i, (name, qty) in enumerate(order):
            if name == item_name:
                order[i] = (name, qty + quantity)
                break
        else:
            order.append((item_name, quantity))

        receipt = create_receipt(order)
        await update.message.reply_text(
            f"Ваш заказ:\n{receipt}",
            reply_markup=menu_markup
        )
        return CATEGORY

    except ValueError:
        await update.message.reply_text("Введите корректное количество (целое число больше 0).")
        return QUANTITY


def create_receipt(order):
    total = 0
    lines = []
    for item, qty in order:
        price = next((v for cat in prices.values() for k, v in cat.items() if k == item), 0)
        item_total = price * qty
        total += item_total
        lines.append(f"{item} x {qty} = {item_total} ₽")
    lines.append(f"Итого: {total} ₽")
    return '\n'.join(lines)


async def handle_confirm(update, context):
    query = update.callback_query
    await query.answer()

    if context.user_data['type'] == 'Заказать доставку':
        type_order = 'Доставка'
    else:
        type_order = 'Заказ с собой'
    order = context.user_data['order']
    receipt = create_receipt(order)

    await query.edit_message_text(text=receipt)

    # Отправляем сообщение покупателю
    user_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Ваш заказ отправлен!\nСтатус Вашего заказа: Не подтвержден"
    )

    # Сохраняем ID сообщения пользователя
    context.user_data['user_message_id'] = user_message.message_id

    # Отправляем сообщение в группу с кнопкой "Подтвердить заказ"
    group_message = await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"Тип заказа: {type_order}\nЗаказ:\n{receipt}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Подтвердить заказ', callback_data=f"confirm_{user_message.chat.id}")]
        ])
    )

    # Сохраняем ID сообщения в группе
    context.user_data['group_message_id'] = group_message.message_id

    return TYPE


async def handle_address(update, context):
    address = update.message.text
    context.user_data['address'] = address
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Введите свой номер телефона')
    return PHONE


async def handle_phone(update, context):
    phone = update.message.text
    context.user_data['phone'] = phone
    receipt = create_receipt(context.user_data['order'])
    receipt += f'\nАдрес: {context.user_data["address"]}'
    receipt += f'\nНомер телефона: {phone}'
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=receipt,
                                   reply_markup=InlineKeyboardMarkup([
                                       [InlineKeyboardButton('Подтвердить', callback_data='accept')],
                                       [InlineKeyboardButton('Изменить данные', callback_data='reject')]
                                   ]))
    return CONFIRMATION


async def handle_status_update(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action, user_chat_id = data[0], int(data[1])

    if action == 'confirm':
        # Обновляем сообщение пользователя
        user_message_id = context.user_data.get('user_message_id')
        if user_message_id:
            await context.bot.edit_message_text(
                chat_id=user_chat_id,
                message_id=user_message_id,
                text="Статус Вашего заказа: Подтвержден"
            )

        # Обновляем сообщение в группе
        group_message_id = context.user_data.get('group_message_id')
        if group_message_id:
            await query.edit_message_text(
                text=query.message.text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('Начали готовить', callback_data=f"cooking_{user_chat_id}")]
                ])
            )
    elif action == 'cooking':
        user_message_id = context.user_data['user_message_id']
        if user_message_id:
            await context.bot.edit_message_text(
                chat_id=user_chat_id,
                message_id=user_message_id,
                text="Статус Вашего заказа: Готовиться"
            )
            # Обновляем сообщение в группе
            group_message_id = context.user_data['group_message_id']
            if group_message_id:
                await query.edit_message_text(
                    text=query.message.text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Отправили доставку', callback_data=f"delivery_{user_chat_id}")],
                        [InlineKeyboardButton('Заказ готов', callback_data=f'ready_{user_chat_id}')]
                    ])
                )
    elif action == 'delivery':
        user_message_id = context.user_data['user_message_id']
        if user_message_id:
            await context.bot.edit_message_text(
                chat_id=user_chat_id,
                message_id=user_message_id,
                text="Статус Вашего заказа: Курьер выехал"
            )
            # Обновляем сообщение в группе
            group_message_id = context.user_data['group_message_id']
            if group_message_id:
                await query.edit_message_text(
                    text=query.message.text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Заказ готов', callback_data=f'ready_{user_chat_id}')]
                    ])
                )
    elif action == 'ready':
        user_message_id = context.user_data['user_message_id']
        if user_message_id:
            await context.bot.edit_message_text(
                chat_id=user_chat_id,
                message_id=user_message_id,
                text="Статус Вашего заказа: Готов"
            )

            # Обновляем сообщение в группе
            group_message_id = context.user_data['group_message_id']
            if group_message_id:
                await query.edit_message_text(
                    text=query.message.text
                )
        return TYPE


async def cancel(update, context):
    return ConversationHandler.END


application = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & (~filters.COMMAND), handle_button_press)],
    states={
        TYPE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_button_press)],
        CATEGORY: [CallbackQueryHandler(callback_handler)],
        ITEM: [CallbackQueryHandler(callback_handler)],
        QUANTITY: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_quantity)],
        ADDRESS: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_address)],
        PHONE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_phone)],
        CONFIRMATION: [CallbackQueryHandler(handle_confirm)]
    },
    fallbacks=[],
)
application.add_handler(CommandHandler('start', start))
application.add_handler(conv_handler)
application.add_handler(CallbackQueryHandler(handle_status_update))

if __name__ == "__main__":
    application.run_polling()
