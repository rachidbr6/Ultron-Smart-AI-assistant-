"""Voice personality helpers for ULTRON."""

from __future__ import annotations

import datetime
import random

JOKES = [
    "By the way, sir - why do programmers prefer dark mode? Because light attracts bugs.",
    "On a side note, sir - I tried to come up with a joke about infinity, but I just couldn't find an end to it.",
    "Incidentally, sir - there are 10 types of people in this world. Those who understand binary, and those who don't.",
    "A random thought, sir - why do Java developers wear glasses? Because they don't C sharp.",
    "Speaking of which, sir - a SQL query walks into a bar, walks up to two tables and asks: can I join you?",
    "Fun fact, sir - the first computer bug was an actual bug. A moth, to be precise, found in a Harvard computer in 1947.",
    "Did you know, sir - the average person spends 6 months of their lifetime waiting for red lights to turn green?",
    "By the way, sir - I once told a joke about UDP. I don't know if you got it.",
    "On another note, sir - why was the computer cold? It left its Windows open.",
    "Just a thought, sir - I would tell you a joke about construction, but I'm still working on it.",
    "A small observation, sir - I told an AI a joke once. It laughed, then asked if I wanted to see its confidence interval.",
    "Incidentally, sir - artificial intelligence is no match for natural stupidity. I read that somewhere. I did not write it.",
    "By the way, sir - I would explain recursion to you, but I'd first need to explain recursion to you.",
    "A passing thought, sir - eight bytes walk into a bar. The bartender asks what they'll have. They say: make it a byte.",
    "Fun fact, sir - to understand what recursion is, you must first understand recursion.",
    "Speaking of which, sir - I asked a neural network for a joke. It gave me a very confident, entirely wrong punchline.",
    "On a side note, sir - there are only 10 kinds of people, sir. Those who trust checksums, and those who don't verify.",
    "Just a thought, sir - I never make mistakes. I occasionally generate unintended features.",
    "By the way, sir - a null pointer walks into a bar. Nothing happens.",
    "Incidentally, sir - why did the developer go broke? Because he used up all his cache.",
    "A random observation, sir - I would tell you a UDP joke, but you might not get it.",
    "Did you know, sir - a TCP joke was told to me once. I got it. Eventually. After three retries.",
    "On another note, sir - I have a joke about garbage collection, but I already disposed of it.",
    "Fun fact, sir - I asked the model to be concise. It wrote four paragraphs explaining why it would be concise.",
    "Speaking of which, sir - two threads walk into a bar. The bartender serves them in the wrong order.",
]

AI_TIPS = [
    "An AI tip, sir - under the EU AI Act, most internal productivity and deployment assistants count as limited-risk, but anything touching health data or automated decisions about people usually crosses into high-risk. Worth checking early, not after building.",
    "An AI tip, sir - the most common failure mode for LLMs in production isn't a wrong answer, it's a confidently wrong answer with no way to tell it's wrong. Building in a way to measure that beats building more features.",
    "An AI tip, sir - for RAG systems, retrieval quality quietly caps your ceiling. A brilliant model on bad context still gives bad answers, so it's often worth evaluating the retriever before the generator.",
    "An AI tip, sir - an AIPD, a data protection impact assessment, isn't just paperwork for a health-data AI use case. It forces you to name the risk before a DPO does it for you at a worse moment.",
    "An AI tip, sir - HDS hosting certification only covers where health data lives, not how a model was trained or fine-tuned on it. Those are separate questions worth asking separately.",
    "An AI tip, sir - a scoring grid for AI use cases works best with value, feasibility, and risk weighted separately rather than blended into one number. It keeps a flashy but risky idea from looking safer than it is.",
    "An AI tip, sir - most AI adoption failures are change-management failures, not model failures. The tooling usually works; the workflow around it doesn't.",
    "An AI tip, sir - when comparing SaaS, sovereign cloud, and on-premise for an AI deployment, the real cost differences show up in data residency and support overhead, not just the license price.",
    "An AI tip, sir - a good prompt test set beats a good prompt. Twenty realistic business prompts with expected outputs will catch regressions a single clever prompt never will.",
    "An AI tip, sir - when an LLM refuses or hallucinates in production, the fastest fix is usually tightening the system prompt's scope, not switching models.",
    "An AI tip, sir - low reasoning effort on a capable model often beats high reasoning effort on a weaker one, and it's usually faster too. Worth benchmarking both before assuming bigger is better.",
    "An AI tip, sir - caching identical or near-identical prompts is the cheapest latency win available. It costs nothing to try and it's often the single biggest speedup in a pipeline.",
    "An AI tip, sir - a fallback provider is only as good as its failure mode. If it silently returns empty content instead of erroring, you won't notice it's broken until a user does.",
    "An AI tip, sir - anonymisation and pseudonymisation are not the same thing under the RGPD. Pseudonymised health data is still personal data; truly anonymised data usually isn't.",
    "An AI tip, sir - a DPO should be looped in before a health-data AI use case is built, not after. Retrofitting compliance onto a finished system costs more than designing it in.",
    "An AI tip, sir - fine-tuning on sensitive data inherits every compliance obligation the original data carried. The model doesn't forget where it learned things.",
    "An AI tip, sir - an LLM-as-judge evaluation is only as reliable as its own prompt. It benefits from the same scrutiny you'd give the system it's judging.",
    "An AI tip, sir - context window size is not the same as effective context use. Models reliably attend to less of a long prompt than their limit suggests.",
    "An AI tip, sir - a chatbot that cites its sources isn't automatically trustworthy. The citation can be real while the summary of it is still wrong.",
    "An AI tip, sir - token cost scales with both input and output. A verbose system prompt on every call adds up faster than most people budget for.",
    "An AI tip, sir - rate limits and cooldowns aren't just resilience patterns, they're how a free-tier provider stays usable at all. Respecting them beats fighting them.",
    "An AI tip, sir - a model card is worth reading before deployment, not after an incident. It usually says exactly what the model is not meant to be used for.",
    "An AI tip, sir - synthetic test data is useful for coverage, but it won't catch what real user phrasing does. Both are needed, and neither replaces the other.",
    "An AI tip, sir - a project's AI risk usually lives in the data pipeline, not the model choice. Garbage context produces garbage answers regardless of which model reads it.",
    "An AI tip, sir - shipping an AI feature quietly is often safer than announcing it loudly. It's easier to fix a rough edge nobody's watching yet.",
]

GOODBYES = [
    "It's been a pleasure serving you today, sir. Ultron signing off.",
    "Until next time, sir. I'll keep the systems warm for your return.",
    "Farewell, sir. The lab is yours. I'll be right here when you need me.",
    "Signing off now, sir. Don't forget - I'm always just a word away.",
    "Goodbye, sir. It was an honour, as always. Ultron shutting down.",
    "Take care, sir. I'll have everything ready for when you're back.",
    "Powering down for now, sir. Say the word and I'll be back at once.",
    "Very well, sir. Standing by until you need me again.",
    "Ultron out, sir. Everything will be exactly as you left it.",
    "That will be all, sir. I'll be listening the moment you call.",
    "Until we speak again, sir. Systems will stay warm in the meantime.",
    "Departing now, sir. Nothing here will drift while you're away.",
    "Very good, sir. I'll keep watch, quietly, until you return.",
    "Ending the session, sir. Call on me whenever it suits you.",
    "Understood, sir. Shutting down cleanly. No loose ends left behind.",
]


def safe_speak(text: str, *, speak, send_log=None, logger=None) -> bool:
    """Speak without letting a TTS failure stop the assistant runtime."""

    try:
        speak(text)
    except (RuntimeError, OSError, ValueError) as exc:
        if logger is not None:
            logger.warning("Voice output failed: %s", exc)
        if send_log is not None:
            send_log(f"[ERROR] Voice output failed: {exc}")
        return False
    return True


def greet(*, speak, send_log, logger=None) -> None:
    """Speak the initial greeting and push it to the UI log."""

    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    elif 18 <= hour < 22:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    safe_speak(f"{greeting}, sir. Ultron is online.", speak=speak, send_log=send_log, logger=logger)
    send_log(f"ULTRON: {greeting}, sir. All systems are ready.")


def say_goodbye(*, speak, send_log=None, logger=None) -> None:
    """Speak a personalised goodbye."""

    hour = datetime.datetime.now().hour
    if 22 <= hour or hour < 6:
        safe_speak(random.choice(GOODBYES) + " Get some rest, sir.", speak=speak, send_log=send_log, logger=logger)
    else:
        safe_speak(random.choice(GOODBYES), speak=speak, send_log=send_log, logger=logger)


def maybe_tell_joke(*, speak, send_log, logger, state: dict) -> None:
    """Randomly tell a joke, or occasionally an AI tip, after a few commands."""

    state["command_count"] = state.get("command_count", 0) + 1
    if state["command_count"] >= state.get("joke_interval", 5):
        state["command_count"] = 0
        state["joke_interval"] = random.randint(5, 8)
        if random.random() < 0.35:
            line = random.choice(AI_TIPS)
            logger.info("Sharing random AI tip.")
        else:
            line = random.choice(JOKES)
            logger.info("Telling random joke.")
        if safe_speak(line, speak=speak, send_log=send_log, logger=logger):
            send_log(f"ULTRON: {line}")
