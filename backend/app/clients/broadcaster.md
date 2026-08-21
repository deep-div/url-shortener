# Redis Pub/Sub Broadcast Flow

                              Redis
                                │
                                │ 1 PSUBSCRIBE pattern
                                │ "analytics:*"
                                ▼
                     ┌──────────────────────┐
                     │     Broadcaster      │
                     │                      │
                     │ ONE Redis pattern    │
                     │     subscription    │
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Channel: code1    Channel: code2    Channel: code3
       analytics:code1   analytics:code2   analytics:code3
              │                 │                 │
        ┌─────┼─────┐     ┌─────┼─────┐     ┌─────┼─────┐
        ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
      Queue  Queue Queue Queue Queue Queue Queue Queue Queue
        A      B     C     A     B     C     A     B     C
        │      │     │     │     │     │     │     │     │
        ▼      ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
       WS     WS    WS    WS    WS    WS    WS    WS    WS
        │      │     │     │     │     │     │     │     │
        ▼      ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
      User   User  User  User  User  User  User  User  User


       Channel: code4              Channel: code5
       analytics:code4             analytics:code5
              │                           │
        ┌─────┼─────┐               ┌─────┼─────┐
        ▼     ▼     ▼               ▼     ▼     ▼
      Queue  Queue Queue           Queue  Queue Queue
        A      B     C               A      B     C
        │      │     │               │      │     │
        ▼      ▼     ▼               ▼      ▼     ▼
       WS     WS    WS              WS     WS    WS
        │      │     │               │      │     │
        ▼      ▼     ▼               ▼      ▼     ▼
      User   User  User            User   User  User


                              ...
                               │
                               ▼
                     Channel: code10
                     analytics:code10
                               │
                         ┌─────┼─────┐
                         ▼     ▼     ▼
                       Queue Queue Queue
                         A     B     C
                         │     │     │
                         ▼     ▼     ▼
                        WS    WS    WS
                         │     │     │
                         ▼     ▼     ▼
                       User  User  User


# Hierarchy

1 PSUBSCRIBE pattern
        │
        ├── analytics:code1  → multiple queues → WebSockets
        ├── analytics:code2  → multiple queues → WebSockets
        ├── analytics:code3  → multiple queues → WebSockets
        ├── analytics:code4  → multiple queues → WebSockets
        ├── analytics:code5  → multiple queues → WebSockets
        ├── analytics:code6  → multiple queues → WebSockets
        ├── analytics:code7  → multiple queues → WebSockets
        ├── analytics:code8  → multiple queues → WebSockets
        ├── analytics:code9  → multiple queues → WebSockets
        └── analytics:code10 → multiple queues → WebSockets


# Example: One Click on code5

Visitor clicks code5
        │
        ▼
Redis PUBLISH
"analytics:code5"
        │
        ▼
Broadcaster
        │
        │ extracts "code5"
        ▼
_subscribers["code5"]
        │
        ├── Queue A → WebSocket A → Dashboard A
        ├── Queue B → WebSocket B → Dashboard B
        └── Queue C → WebSocket C → Dashboard C

The message is routed only to the queues belonging to code5.