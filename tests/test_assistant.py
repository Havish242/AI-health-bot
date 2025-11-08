import pytest
from assistant import HealthAssistant


def test_empty_message():
    a = HealthAssistant()
    r = a.respond("")
    assert "didn't" in r.lower() or "didn't get" in r.lower()


def test_greeting():
    a = HealthAssistant()
    r = a.respond("hi there")
    assert "hello" in r.lower() or "i'm" in r.lower()


def test_emergency():
    a = HealthAssistant()
    r = a.respond("I have chest pain and can't breathe")
    assert "emergency" in r.lower() or "call" in r.lower()


def test_fever():
    a = HealthAssistant()
    r = a.respond("I have a fever and cough")
    assert "fever" in r.lower() or "infection" in r.lower()
