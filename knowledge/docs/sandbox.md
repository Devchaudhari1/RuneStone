# Sandbox

RuneStone executes potentially unsafe commands inside a Docker sandbox.

The sandbox uses a dedicated non-root user named runestone.

## Isolation

Sandbox containers use network isolation so commands cannot access the external network.

The container filesystem is read-only except for the mounted workspace and a temporary filesystem.

Linux capabilities are dropped from the container.

## Resource Limits

The sandbox limits memory, CPU usage, and the number of processes.

Commands also have a configurable timeout to prevent indefinitely running processes.

## Workspace

The RuneStone workspace is mounted at /workspace inside the container.

Commands are executed relative to the requested workspace directory.