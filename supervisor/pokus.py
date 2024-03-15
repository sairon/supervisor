import asyncio
from contextlib import asynccontextmanager

from aiohttp import ClientSession, ClientTimeout, ClientResponse
from aiohttp.hdrs import ACCEPT, RANGE

from supervisor.host.const import LogFormat, LogFormatter
from supervisor.utils.systemd_journal import journal_logs_reader


@asynccontextmanager
async def journald_logs(
    path: str = "/entries",
    params: dict[str, str | list[str]] | None = None,
    range_header: str | None = None,
    accept: LogFormat = LogFormat.JOURNAL,
    timeout: ClientTimeout | None = None,
) -> ClientResponse:
    """Get logs from systemd-journal-gatewayd.
    See https://www.freedesktop.org/software/systemd/man/systemd-journal-gatewayd.service.html for params and more info.
    """
    async with ClientSession() as session:
        headers = {ACCEPT: accept}
        if range_header:
            headers[RANGE] = range_header
        async with session.get(
            f"http://localhost:19531{path}",
            headers=headers,
            params=params or {},
            timeout=timeout,
        ) as client_response:
            yield client_response


async def main():
    async with journald_logs(range_header=":-100:", params=None) as resp:
        async for line in journal_logs_reader(resp, LogFormatter.VERBOSE):
            print(line)


if __name__ == "__main__":
    asyncio.run(main())
