from aiogram.fsm.state import State, StatesGroup

class FilterStates(StatesGroup):
    menu = State()
    waiting_budget = State()
    waiting_rooms = State()
    waiting_parking = State()
    waiting_pets = State()
    waiting_elevator = State()
    waiting_floor = State()