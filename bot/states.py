from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    confirm = State()


class QuickReplyStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()


class EditPriceStates(StatesGroup):
    waiting_for_text = State()
