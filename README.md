# WorldCash Crypto-to-Cash Kiosk

A complete crypto-to-cash kiosk system built for Raspberry Pi 4B with Telequip T-Flex coin dispenser integration. Converts cryptocurrency to physical cash via World ID verification and automated coin dispensing.

## System Architecture

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React Frontend
    participant Backend as Flask Backend  
    participant WorldID as World ID API
    participant Wallet as Wallet API
    participant Hardware as T-Flex Dispenser

    User->>Frontend: Select withdrawal amount
    Frontend->>Backend: GET /api/balance
    Backend->>Wallet: Check user balance
    Wallet-->>Backend: Balance data
    Backend-->>Frontend: USD + crypto balance

    User->>Frontend: Initiate withdrawal
    Frontend->>User: Show World ID QR code
    User->>WorldID: Scan QR with app
    WorldID->>Frontend: Verification proof
    
    Frontend->>Backend: POST /api/withdraw {proof, amount}
    Backend->>WorldID: Verify proof
    WorldID-->>Backend: Verification result
    Backend->>Wallet: Lock user tokens
    Wallet-->>Backend: Lock confirmed
    
    Backend->>Hardware: Dispense coins
    Hardware-->>Backend: Coins dispensed
    Backend->>Wallet: Settle transaction
    Wallet-->>Backend: Settlement confirmed
    Backend-->>Frontend: Success response
    Frontend->>User: Show success + collect cash
