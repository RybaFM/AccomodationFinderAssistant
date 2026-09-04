from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

ROOM_OPTIONS = ["1", "2", "3", "4"]
FLOOR_OPTIONS = ["1", "2-5", "6-10", "10"]

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

def multiselect_kb(options: list[str], selected: set | None, prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for opt in options:
        is_selected = selected is not None and opt in selected
        text = f"✅ {opt}" if is_selected else opt
        builder.button(text=text, callback_data=f"{prefix}:{opt}")

    no_text = "✅ No 🚫" if selected is None else "No 🚫"
    builder.button(text=no_text, callback_data=f"{prefix}:none")
    builder.button(text="⬅️ Back to menu", callback_data=f"{prefix}:back")
    builder.adjust(2, 1)
    return builder.as_markup()

def yes_no_kb(prefix: str, current: bool | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    yes_text = "✅ Yes" if current is True else "Yes"
    no_text = "✅ No" if current is False else "No"
    builder.button(text=yes_text, callback_data=f"{prefix}:yes")
    builder.button(text=no_text, callback_data=f"{prefix}:no")
    builder.button(text="⬅️ Back to menu", callback_data=f"{prefix}:back")
    builder.adjust(2, 1)
    return builder.as_markup()