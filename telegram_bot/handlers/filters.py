from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from telegram_bot.keyboards.filters_kb import multiselect_kb,yes_no_kb, ROOM_OPTIONS, FLOOR_OPTIONS
from telegram_bot.states.filter_states import FilterStates
from telegram_bot.handlers.start import show_menu, router


router = Router()

@router.callback_query(FilterStates.menu,F.data.startswith("menu:"))
async def open_menu(callback_query: CallbackQuery,state: FSMContext):
    request = callback_query.data.split(":")[1]

    #if request == "search": потом
    data = await state.get_data()
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
        await callback_query.message.edit_text(labels[request], reply_markup=yes_no_kb(request,data.get(request))) #kb
    elif request == "rooms":
        await state.set_state(FilterStates.waiting_rooms)
        data = await state.get_data()
        current = data.get("rooms")
        await callback_query.message.edit_text(
            "How many bedrooms?", reply_markup= multiselect_kb(ROOM_OPTIONS,current,"rooms")
        )
    elif request == "floor":
        await state.set_state(FilterStates.waiting_floor)
        data = await state.get_data()
        current = data.get("floor")
        await callback_query.message.edit_text(
            "Which floors do you like?", reply_markup=multiselect_kb(FLOOR_OPTIONS,current,"floor")
        )

    await callback_query.answer()

@router.message(FilterStates.waiting_budget)
async def set_budget(message: Message,state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Please enter a number")
        return
    await state.update_data(budget=int(message.text))
    await state.set_state(FilterStates.menu)
    await show_menu(message,state)

@router.callback_query(FilterStates.waiting_rooms, F.data.startswith("rooms:"))
async def set_rooms(callback_query: CallbackQuery, state: FSMContext):
    value = callback_query.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("rooms")

    if value == "back":
        await state.set_state(FilterStates.menu)
        await show_menu(callback_query.message, state)
        await callback_query.answer()
        return

    if value == "none":
        selected = set() if selected is None else None
        await state.update_data(rooms=selected)
        await callback_query.message.edit_reply_markup(
            reply_markup=multiselect_kb(ROOM_OPTIONS, selected, "rooms")
        )
        await callback_query.answer()
        return

    if selected is None:
        selected = set()
    selected ^= {value}
    if not selected:
        selected = None

    await state.update_data(rooms=selected)
    await callback_query.message.edit_reply_markup(
        reply_markup=multiselect_kb(ROOM_OPTIONS, selected, "rooms")
    )
    await callback_query.answer()

@router.callback_query(FilterStates.waiting_floor, F.data.startswith("floor:"))
async def set_floor(callback_query: CallbackQuery, state: FSMContext):
    value = callback_query.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("floor")

    if value == "back":
        await state.set_state(FilterStates.menu)
        await show_menu(callback_query.message, state)
        await callback_query.answer()
        return

    if value == "none":
        selected = set() if selected is None else None
        await state.update_data(floor=selected)
        await callback_query.message.edit_reply_markup(
            reply_markup=multiselect_kb(FLOOR_OPTIONS, selected, "floor")
        )
        await callback_query.answer()
        return

    if selected is None:
        selected = set()
    selected ^= {value}
    if not selected:
        selected = None

    await state.update_data(floor=selected)
    await callback_query.message.edit_reply_markup(
        reply_markup=multiselect_kb(FLOOR_OPTIONS, selected, "floor")
    )
    await callback_query.answer()

@router.callback_query(FilterStates.waiting_parking, F.data.startswith("parking:"))
async def set_parking(callback_query: CallbackQuery, state: FSMContext):
    await _toggle_bool_field(callback_query, state, "parking")


@router.callback_query(FilterStates.waiting_pets, F.data.startswith("pets:"))
async def set_pets(callback_query: CallbackQuery, state: FSMContext):
    await _toggle_bool_field(callback_query, state, "pets")


@router.callback_query(FilterStates.waiting_elevator, F.data.startswith("elevator:"))
async def set_elevator(callback_query: CallbackQuery, state: FSMContext):
    await _toggle_bool_field(callback_query, state, "elevator")

async def _toggle_bool_field(callback_query: CallbackQuery, state: FSMContext, field: str):
    choice = callback_query.data.split(":")[1]

    if choice == "back":
        await state.set_state(FilterStates.menu)
        await show_menu(callback_query.message, state)
        await callback_query.answer()
        return

    data = await state.get_data()
    current = data.get(field)
    new_value = (choice == "yes")

    if current == new_value:
        new_value = None

    await state.update_data({field: new_value})
    await callback_query.message.edit_reply_markup(reply_markup=yes_no_kb(field, new_value))
    await callback_query.answer()