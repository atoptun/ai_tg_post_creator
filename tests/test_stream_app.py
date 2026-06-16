from pydantic import ValidationError
import pytest
from faststream.rabbit import TestRabbitBroker

from app.stream_app import broker

WITH_REAL=False
# WITH_REAL=True

@pytest.mark.asyncio()
async def test_handle() -> None:
    async with TestRabbitBroker(broker, with_real=WITH_REAL) as br:
        with pytest.raises(ValueError):
            await br.publish("hello!", "test-queue")


@pytest.mark.asyncio()
async def test_user_handle() -> None:
    from app.stream_app import user_handler

    async with TestRabbitBroker(broker, with_real=WITH_REAL) as br:
        await br.publish({"user_id": 123, "name": "Alice"}, "test-user-queue")
        await user_handler.wait_call(timeout=5)

        user_handler.mock.assert_called_once_with({"name": "Alice", "user_id": 123})

    assert not user_handler.mock.called  # mock is reset


@pytest.mark.asyncio()
async def test_user_handle_error() -> None:
    from app.stream_app import user_handler

    async with TestRabbitBroker(broker, with_real=WITH_REAL) as br:
        with pytest.raises(ValidationError):
            await br.publish('wrong message', "test-user-queue")
            await user_handler.wait_call(timeout=5)

        user_handler.mock.assert_called_once_with("wrong message")

    assert not user_handler.mock.called  # mock is reset