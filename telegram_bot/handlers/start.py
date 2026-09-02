from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telegram_bot.keyboards.filters_kb import filters_menu_kb
from telegram_bot.states.filter_states import FilterStates
router = Router()

DEFAULT_FILTERS = {
    "budget": None, "rooms": None, "floor": None,
    "parking": None, "pets": None, "elevator": None
}
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(**DEFAULT_FILTERS)
    await state.set_state(FilterStates.menu)
    await show_menu(message, state)

async def show_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    text = build_menu_text(data)
    keyboard = filters_menu_kb()
    if isinstance(message, CallbackQuery):
        try:
            await message.message.edit_text(text, reply_markup=keyboard)
        except Exception:
            pass
        await message.answer()
    else:
        await message.answer(text, reply_markup=keyboard)

def build_menu_text(data: dict) -> str:
    def formatation(variabel):
        if variabel is None:
            return "Not selected"
        if isinstance(variabel, bool):
            return "yes" if variabel else "no"
        if isinstance(variabel, set):
            return ", ".join(variabel) if variabel else "Not selected"
        return str(variabel)
    return ("You can find an apartment here.\n"
            "You can use these filters to help you search.\n"
            f"Budget: {formatation(data['budget'])}\n"
            f"Rooms: {formatation(data['rooms'])}\n"
            f"Floor: {formatation(data['floor'])}\n"
            f"Parking: {formatation(data['parking'])}\n"
            f"Elevator: {formatation(data['elevator'])}\n"
            f"Pets: {formatation(data['pets'])}\n"
            "Choose what to configure, and once you've made your selection, start the search.\n"
            )
