"""Test systemd journal utilities."""
import asyncio
from unittest.mock import MagicMock

from supervisor.host.const import LogFormatter
from supervisor.utils.systemd_journal import journal_logs_reader

from tests.common import load_fixture


def _journal_logs_mock():
    stream = asyncio.StreamReader(loop=asyncio.get_running_loop())
    journal_logs = MagicMock()
    journal_logs.__aenter__.return_value.content = stream
    return journal_logs


async def test_format_simple():
    """Test plain formatter."""
    journal_logs = _journal_logs_mock()
    stream = journal_logs.__aenter__.return_value.content
    stream.feed_data(b"MESSAGE=Hello, world!\n\n")
    line = await anext(journal_logs_reader(journal_logs))
    assert line == "Hello, world!"


async def test_format_verbose():
    """Test verbose formatter."""
    journal_logs = _journal_logs_mock()
    stream = journal_logs.__aenter__.return_value.content
    stream.feed_data(
        b"__REALTIME_TIMESTAMP=1379403171000000\n"
        b"_HOSTNAME=homeassistant\n"
        b"SYSLOG_IDENTIFIER=python\n"
        b"_PID=666\n"
        b"MESSAGE=Hello, world!\n\n"
    )
    line = await anext(
        journal_logs_reader(journal_logs, log_formatter=LogFormatter.VERBOSE)
    )
    assert line == "2013-09-17 09:32:51.000 homeassistant python[666]: Hello, world!"


async def test_journal_logs_reader():
    """Test reading and formatting using journal logs reader."""
    journal_logs = _journal_logs_mock()
    stream = journal_logs.__aenter__.return_value.content
    stream.feed_data(
        b"ID=1\n"
        b"MESSAGE\n\x0d\x00\x00\x00\x00\x00\x00\x00Hello,\nworld!\n"
        b"AFTER=after\n\n"
    )

    line = await anext(journal_logs_reader(journal_logs))
    assert line == "Hello,\nworld!"


async def test_journal_logs_reader_two_messages():
    """Test reading multiple messages."""
    journal_logs = _journal_logs_mock()
    stream = journal_logs.__aenter__.return_value.content
    stream.feed_data(
        b"MESSAGE=Hello, world!\n"
        b"ID=1\n\n"
        b"MESSAGE=Hello again, world!\n"
        b"ID=2\n\n"
    )

    reader = journal_logs_reader(journal_logs)
    assert await anext(reader) == "Hello, world!"
    assert await anext(reader) == "Hello again, world!"


async def test_streamreader_mock2():
    journal_logs = _journal_logs_mock()
    stream = journal_logs.__aenter__.return_value.content
    stream.feed_data(load_fixture("logs_export_host.txt").encode("utf-8"))
    line = await anext(journal_logs_reader(journal_logs))
    assert line == "Started Hostname Service."
