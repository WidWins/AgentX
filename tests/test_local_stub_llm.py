import asyncio
import unittest

from livekit.agents import llm

from local_stub_llm import LocalStubLLM, _build_local_reply, _latest_user_text


class LocalStubLLMTests(unittest.TestCase):
    def test_extract_latest_user_text(self):
        ctx = llm.ChatContext()
        ctx.add_message(role="system", content="system prompt")
        ctx.add_message(role="user", content="  hello world  ")
        ctx.add_message(role="assistant", content="how can I help?")

        self.assertEqual(_latest_user_text(ctx), "hello world")

    def test_build_reply_empty_ctx(self):
        ctx = llm.ChatContext()
        reply = _build_local_reply(ctx)
        self.assertIn("Local mode is active", reply)
        self.assertIn("Tell me your idea", reply)

    def test_build_reply_with_user_context(self):
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content="Building a new fintech app")
        reply = _build_local_reply(ctx)
        self.assertIn("Idea: Building a new fintech app", reply)
        self.assertIn("What specific pain are they facing today", reply)

    def test_llm_metadata(self):
        stub = LocalStubLLM()
        self.assertEqual(stub.model, "wid-wins-local-stub")
        self.assertEqual(stub.provider, "local")

    def test_intro_with_name_gets_personalized_reply(self):
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content="im aakash")
        reply = _build_local_reply(ctx)
        self.assertIn("Nice to meet you, Aakash", reply)
        self.assertIn("full qualification flow", reply)

    def test_intro_like_business_statement_is_not_treated_as_name(self):
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content="im building business school")
        reply = _build_local_reply(ctx)
        self.assertNotIn("Nice to meet you", reply)
        self.assertIn("Idea: im building business school", reply)

    def test_full_conversation_returns_recommendation(self):
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content="I am building an AI assistant for clinics")
        ctx.add_message(role="user", content="The main problem is clinics lose time on manual scheduling")
        ctx.add_message(role="user", content="Target users are small clinic owners")
        ctx.add_message(role="user", content="Our goal is to launch a paid pilot in 60 days")
        ctx.add_message(role="user", content="We are in execution stage and ready to invest with premium budget")
        reply = _build_local_reply(ctx)
        self.assertIn("looks like a", reply)
        self.assertIn("best starting package", reply)

    def test_chat_returns_stream(self):
        async def _create_stream():
            stub = LocalStubLLM()
            ctx = llm.ChatContext()
            stream = stub.chat(chat_ctx=ctx)
            self.assertIsInstance(stream, llm.LLMStream)

        asyncio.run(_create_stream())


class LocalStubLLMAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_consume_stream(self):
        stub = LocalStubLLM()
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content="test-message")
        stream = stub.chat(chat_ctx=ctx)

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

        self.assertTrue(len(chunks) > 0)

        full_content = "".join([c.delta.content for c in chunks if c.delta and c.delta.content])
        self.assertIn("test-message", full_content)

    async def test_empty_context_stream(self):
        stub = LocalStubLLM()
        ctx = llm.ChatContext()
        stream = stub.chat(chat_ctx=ctx)

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

        full_content = "".join([c.delta.content for c in chunks if c.delta and c.delta.content])
        self.assertIn("Tell me your idea", full_content)
