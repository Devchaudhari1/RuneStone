FROM python:3.13-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pytest

# Create an unprivileged user for sandbox execution.
RUN useradd --create-home --uid 10001 runestone

RUN chown -R runestone:runestone /workspace

USER runestone

CMD ["python", "--version"]