# Redis Pub/Sub Broadcast Flow
##### Advantages:
1. Isolation between SSE clients: Each user has their own queue. If one user's connection is slow or frozen, their queue backs up — it does NOT block other users from receiving the snapshot. A slow user in London doesn't delay a fast user in Mumbai.
2. Without Broadcaster:  (connection is Psubscribe, pattern subscription)
10k users → 10k Redis connections → Redis gets hammered
With Broadcaster:
10k users → 1 Redis connection → Redis gets 1 message
                    │
                    └── Broadcaster fans out to 10k queues in-process (no network)
3. Clean disconnect handling
When an SSE connection closes, its queue is simply removed from the set. The Broadcaster doesn't know or care. Next publish just skips that queue because it's gone. No error, no crash, no effect on other users.
4.  Drop policy on slow consumers (QUEUE_MAXSIZE)
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
      SSE    SSE   SSE   SSE   SSE   SSE   SSE   SSE   SSE
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
      SSE    SSE   SSE             SSE    SSE   SSE
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
                        SSE   SSE   SSE
                         │     │     │
                         ▼     ▼     ▼
                       User  User  User

10k clicks on code1
        │
        ▼
10k times: run_url_analytics() → save to DB → publish snapshot to Redis
        │
        ▼
Broadcaster receives 10k snapshots one by one
        │
        └── for each snapshot, puts it on EVERY queue:
                queue_1  ──► user 1 watching dashboard
                queue_2  ──► user 2 watching dashboard
                queue_3  ──► user 3 watching dashboard

# Hierarchy

1 PSUBSCRIBE pattern
        │
        ├── analytics:code1  → multiple queues → SSE clients
        ├── analytics:code2  → multiple queues → SSE clients
        ├── analytics:code3  → multiple queues → SSE clients
        ├── analytics:code4  → multiple queues → SSE clients
        ├── analytics:code5  → multiple queues → SSE clients
        ├── analytics:code6  → multiple queues → SSE clients
        ├── analytics:code7  → multiple queues → SSE clients
        ├── analytics:code8  → multiple queues → SSE clients
        ├── analytics:code9  → multiple queues → SSE clients
        └── analytics:code10 → multiple queues → SSE clients


# Example: One Click on code5

Visitor clicks code5
        │
        ▼
Postgres: save click → commit
        │
        ▼
Postgres: re-query fresh all-time stats (same session)
        │
        ▼
build_live_snapshot() → full JSON snapshot
{ summary: {...}, by_country: {...}, by_device: {...}, ... }
        │
        ▼
Redis PUBLISH "analytics:code5" snapshot
        │
        ▼
Broadcaster._listen()
        │
        │ extracts "code5" from channel name
        ▼
_subscribers["code5"]
        │
        ├── Queue A → SSE A → Dashboard A → setData(snapshot)
        ├── Queue B → SSE B → Dashboard B → setData(snapshot)
        └── Queue C → SSE C → Dashboard C → setData(snapshot)

1 Redis publish. N browsers receive the same snapshot.
Browser replaces state directly — no math, no merging.
