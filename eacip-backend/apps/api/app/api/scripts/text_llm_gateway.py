import asyncio

from app.core.llm_gateway import complete


async def main() -> None:
    result = await complete(
        system_prompt="You are a helpful assistant. Respond in one short sentence.",
        user_prompt="Say hello and confirm you're working.",
    )
    print("✅ Raw LLM response:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
