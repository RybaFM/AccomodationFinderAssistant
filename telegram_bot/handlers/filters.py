from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from urllib3 import request

from telegram_bot.states.filter_states import FilterStates
from telegram_bot.handlers.start import show_menu, router


router = Router()

@router.callback_query(FilterStates.menu,F.data.startswith("menu:"))
async def open_menu(callback_query: CallbackQuery,state: FSMContext):
    request = callback_query.data.split(":")[1]

    #if request == "search": потом

    if request == "budget":
        await state.set_state(FilterStates.waiting_budget)
        await callback_query.message.edit_text("Write your budget (whole number):")
    elif request in ("parking","pets","elevator"):
        state_map = {
            "parking" : FilterStates.waiting_parking,
            "elevator" : FilterStates.waiting_elevator,
            "pets" : FilterStates.waiting_pets
        }
        labels = {
            "parking" : "Do you need a parking spot?",
            "elevator" : "Do you need a parking elevator?",
            "pets" : "Do you need a permit for animals?"
        }
        await state.set_state(state_map[request])
        await callback_query.message.edit_text(labels[request])
    await callback_query.answer()

@router.message(FilterStates.waiting_budget)
async def set_budget(message: Message,state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Please enter a number")
        return
    await state.update_data(budget=int(message.text))
    await state.set_state(FilterStates.menu)
    await show_menu(message,state)