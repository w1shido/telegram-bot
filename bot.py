import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = 8324243196

# Замени ссылки и содержимое delivery на свои легальные цифровые товары.
PRODUCTS = {
    "product1": {
        "name": "AimWare Crack",
        "price": 500,
        "payment_url": "https://funpay.com/lots/offer?id=77385969",
        "delivery": "Ваш товар"
    },
    "product2": {
        "name": "AtackWare Crack",
        "price": 350,
        "payment_url": "https://funpay.com/lots/offer?id=77386114",
        "delivery": "Ваш товар"
    },
    "product3": {
        "name": "Skeet Crack",
        "price": 444,
        "payment_url": "https://funpay.com/lots/offer?id=77385766",
        "delivery": "Ваш товар"
    }
}

orders = {}
next_order_id = 1000


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Купить", callback_data="catalog")],
        [InlineKeyboardButton("❌ Не хочу", callback_data="no")]
    ]

    await update.message.reply_text(
        "Здравствуйте! 👋\n\n"
        "Хотите приобрести цифровой товар?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# КНОПКИ
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global next_order_id

    query = update.callback_query
    await query.answer()

    data = query.data

    # -------------------------
    # КАТАЛОГ
    # -------------------------

    if data == "catalog":
        keyboard = []

        for product_id, product in PRODUCTS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {product['name']} — {product['price']} ₽",
                    callback_data=f"product_{product_id}"
                )
            ])

        await query.edit_message_text(
            "🛍 Выберите товар:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -------------------------
    # ОТКАЗ
    # -------------------------

    elif data == "no":
        await query.edit_message_text(
            "Хорошо 👍\n\n"
            "Если захотите приобрести товар, снова нажмите /start"
        )

    # -------------------------
    # ВЫБОР ТОВАРА
    # -------------------------

    elif data.startswith("product_"):
        product_id = data.replace("product_", "")

        if product_id not in PRODUCTS:
            await query.edit_message_text("❌ Товар не найден.")
            return

        product = PRODUCTS[product_id]

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Оплатить на FanPay",
                    url=product["payment_url"]
                )
            ],
            [
                InlineKeyboardButton(
                    "➡️ Далее",
                    callback_data=f"next_{product_id}"
                )
            ]
        ]

        await query.edit_message_text(
            f"📦 {product['name']}\n\n"
            f"💰 Цена: {product['price']} ₽\n\n"
            "1️⃣ Нажмите «Оплатить на FanPay».\n"
            "2️⃣ Завершите оплату.\n"
            "3️⃣ После этого нажмите «Далее».",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -------------------------
    # ДАЛЕЕ
    # -------------------------

    elif data.startswith("next_"):
        product_id = data.replace("next_", "")

        if product_id not in PRODUCTS:
            await query.edit_message_text("❌ Товар не найден.")
            return

        product = PRODUCTS[product_id]

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Да, оплатил",
                    callback_data=f"paid_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data="catalog"
                )
            ]
        ]

        await query.edit_message_text(
            f"🧾 Товар: {product['name']}\n"
            f"💰 Сумма: {product['price']} ₽\n\n"
            "Вы уже оплатили товар?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -------------------------
    # КЛИЕНТ СООБЩИЛ ОБ ОПЛАТЕ
    # -------------------------

    elif data.startswith("paid_"):
        product_id = data.replace("paid_", "")

        if product_id not in PRODUCTS:
            await query.edit_message_text("❌ Товар не найден.")
            return

        product = PRODUCTS[product_id]

        next_order_id += 1
        order_id = next_order_id

        orders[order_id] = {
            "user_id": query.from_user.id,
            "username": query.from_user.username,
            "product_id": product_id,
            "product_name": product["name"],
            "price": product["price"],
            "status": "waiting"
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Подтвердить платёж",
                    callback_data=f"confirm_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Платёж не подтверждён",
                    callback_data=f"reject_{order_id}"
                )
            ]
        ]

        username = query.from_user.username

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 НОВЫЙ ЗАПРОС НА ПРОВЕРКУ\n\n"
                f"🧾 Заказ №{order_id}\n"
                f"📦 Товар: {product['name']}\n"
                f"💰 Сумма: {product['price']} ₽\n"
                f"👤 Username: @{username if username else 'нет'}\n"
                f"🆔 ID клиента: {query.from_user.id}\n\n"
                "Клиент сообщил, что оплатил."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await query.edit_message_text(
            f"⏳ Заказ №{order_id}\n\n"
            "Ваш запрос отправлен продавцу.\n"
            "Ожидайте проверки платежа."
        )

    # -------------------------
    # ПОДТВЕРДИТЬ
    # -------------------------

    elif data.startswith("confirm_"):
        order_id = int(data.replace("confirm_", ""))

        order = orders.get(order_id)

        if not order:
            await query.answer(
                "Заказ не найден.",
                show_alert=True
            )
            return

        if order["status"] != "waiting":
            await query.answer(
                "Этот заказ уже обработан.",
                show_alert=True
            )
            return

        order["status"] = "confirmed"

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"✅ Платёж подтверждён!\n\n"
                f"🧾 Заказ №{order_id}\n"
                f"📦 {order['product_name']}\n\n"
                "🎁 Ваш товар:\n\n"
                f"{order['delivery'] if 'delivery' in order else PRODUCTS[order['product_id']]['delivery']}"
            )
        )

        await query.edit_message_text(
            f"✅ Заказ №{order_id} подтверждён.\n"
            "Товар отправлен клиенту."
        )

    # -------------------------
    # ОТКЛОНИТЬ
    # -------------------------

    elif data.startswith("reject_"):
        order_id = int(data.replace("reject_", ""))

        order = orders.get(order_id)

        if not order:
            await query.answer(
                "Заказ не найден.",
                show_alert=True
            )
            return

        if order["status"] != "waiting":
            await query.answer(
                "Этот заказ уже обработан.",
                show_alert=True
            )
            return

        order["status"] = "rejected"

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ Платёж по заказу №{order_id} "
                "не подтверждён.\n\n"
                "Попробуйте оплатить товар заново."
            )
        )

        await query.edit_message_text(
            f"❌ Заказ №{order_id} отклонён."
        )


# =========================
# ЗАПУСК
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
