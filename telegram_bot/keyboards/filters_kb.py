from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def filters_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰Budget", callback_data="menu:budget")
    builder.button(text="🛏️Rooms", callback_data="menu:rooms")
    builder.button(text="🏢Floor", callback_data="menu:floor")
    builder.button(text="🚗Parking", callback_data="menu:parking")
    builder.button(text="🐾Pets", callback_data="menu:pets")
    builder.button(text="🛗Elevator", callback_data="menu:elevator")
    builder.button(text="🔍Search", callback_data="menu:search")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()