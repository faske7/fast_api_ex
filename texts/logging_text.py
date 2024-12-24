async def error_send(operator_id, e):
    error_send = f"Ошибка при отправке сообщения оператору {operator_id}: {e}"
    return error_send

no_have_ass = "no have assigned requsets"