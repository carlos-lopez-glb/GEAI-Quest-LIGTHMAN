# LIGHTMAN Mission Terminal

**Agent LIGHTMAN's MiniTel-Lite Network Infiltration System**

## 🎯 Mission Objective

Infiltrate the MiniTel-Lite network and retrieve emergency override codes from the JOSHUA system using authenticated protocol sequences with comprehensive session recording and analysis capabilities.

## 🏗️ Architecture Overview

The LIGHTMAN system follows clean architecture principles with clear separation of concerns:

```
├── lightman.py              # Main mission terminal
├── src/
│   ├── minitel/             # Core protocol implementation
│   │   ├── protocol.py      # Frame encoding/decoding, command definitions
│   │   ├── server.py        # TCP server with state management  
│   │   ├── client.py        # Basic TCP client
│   │   └── enhanced_client.py # Mission-ready client with recording
│   ├── session/             # Session recording and replay
│   │   ├── recorder.py      # Session recording functionality
│   │   └── replay.py        # Session replay engine
│   ├── tui/                 # Text User Interface
│   │   └── replay_app.py    # Interactive session replay TUI
│   └── tests/               # Comprehensive test suite
├── recordings/              # Session recordings directory
└── run_tests.py            # Test runner with coverage analysis
```

## 🚀 Quick Start

### Execute Mission

Connect to target server and retrieve override codes:

```bash
python lightman.py <host> <port> --record
```

Example:
```bash
python lightman.py 192.168.1.100 8080 --record
```

### Test Connection

Verify connectivity without executing full mission:

```bash
python lightman.py <host> <port> --test
```

### Replay Session

Analyze recorded sessions with interactive TUI:

```bash
python lightman.py replay recordings/mission_20250917_124530.json
```

## 📋 Key Features

### 🔒 Enhanced Security
- **SHA-256 Integrity**: All frames validated with cryptographic hashes
- **Nonce Protection**: Strict sequence validation prevents replay attacks
- **Connection Timeout**: 2-second automatic cleanup prevents resource exhaustion
- **Graceful Error Handling**: Robust disconnection and retry logic

### 📝 Session Recording
- **Complete Capture**: All client-server interactions recorded in JSON format
- **Timestamped Records**: Precise timing for each protocol step
- **Payload Analysis**: Both hex and text representation of payloads
- **Mission Replay**: Step-by-step analysis of protocol sequences

### 🎮 Interactive TUI Replay
- **Navigation Controls**: N/P for next/previous, Q to quit, H for help
- **Step Visualization**: Clear display of request/response sequences
- **Progress Tracking**: Visual progress bar and step counters
- **Mission Analysis**: Detailed frame inspection capabilities

### 🛡️ Robust Operation
- **Auto-Reconnection**: Exponential backoff retry logic
- **Disconnection Handling**: Graceful recovery from network failures
- **Connection Pooling**: Support for multiple concurrent connections
- **Resource Management**: Automatic cleanup and memory management

## 🔧 Protocol Implementation

### Frame Structure
```
Wire Format: LEN (2 bytes, big-endian) | DATA_B64 (Base64 encoded)
Binary Frame: CMD (1 byte) | NONCE (4 bytes) | PAYLOAD | HASH (32 bytes SHA-256)
```

### Mission Protocol Sequence
```
1. HELLO (nonce=0) → HELLO_ACK (nonce=1)      # Authentication
2. DUMP (nonce=2) → DUMP_FAILED (nonce=3)     # First attempt (expected failure)
3. DUMP (nonce=4) → DUMP_OK (nonce=5)         # Second attempt (override codes)
4. STOP_CMD (nonce=6) → STOP_OK (nonce=7)     # Acknowledgment
```

### Supported Commands

| Command | Code | Direction | Purpose | Response |
|---------|------|-----------|---------|----------|
| HELLO | 0x01 | Client → Server | Initialize connection | HELLO_ACK (0x81) |
| DUMP | 0x02 | Client → Server | Request override codes | DUMP_FAILED (0x82) / DUMP_OK (0x83) |
| STOP_CMD | 0x04 | Client → Server | Session termination | STOP_OK (0x84) |

## 🧪 Testing & Validation

### Run Complete Test Suite
```bash
python run_tests.py --verbose
```

### Run with Coverage Analysis
```bash
python run_tests.py --coverage
```

**Coverage Requirements**: Minimum 80% test coverage achieved across all modules.

### Individual Test Modules
```bash
python src/tests/test_protocol.py           # Core protocol tests
python src/tests/test_enhanced_client.py    # Enhanced client tests  
python src/tests/test_session_replay.py     # Session recording tests
```

## 📊 Key Design Decisions

### 1. **Enhanced Client Architecture**
- **Rationale**: Separation of basic client (educational) vs enhanced client (mission-critical)
- **Benefits**: Maintains backward compatibility while adding advanced features
- **Implementation**: Dependency injection for session recorder, configurable retry logic

### 2. **Session Recording Strategy**
- **Rationale**: JSON format for human readability and tool compatibility
- **Benefits**: Easy analysis, replay capability, debugging support
- **Implementation**: Structured records with timestamps, hex/text payload representation

### 3. **TUI Replay Design**
- **Rationale**: Terminal-based for secure environments without GUI
- **Benefits**: Works over SSH, lightweight, keyboard-driven navigation
- **Implementation**: Curses-based interface with color coding and progress visualization

### 4. **Error Handling Philosophy**
- **Rationale**: Mission-critical operations require graceful degradation
- **Benefits**: Continues operation despite network issues, comprehensive logging
- **Implementation**: Exponential backoff, connection state tracking, detailed error messages

## 🔍 Edge Case Handling

### Network Disconnections
- **Detection**: Socket errors, timeouts, connection closed
- **Response**: Automatic retry with exponential backoff
- **Recovery**: Session state preservation, graceful cleanup

### Protocol Violations
- **Nonce Mismatches**: Immediate disconnection with detailed logging
- **Invalid Frames**: Hash validation failure handling
- **Malformed Data**: Base64 decode error recovery

### Resource Management
- **Memory Usage**: Bounded session recording, automatic cleanup
- **File Handles**: Proper socket and file descriptor management
- **Thread Safety**: Safe concurrent operation

## 🛠️ Development Standards

### Code Quality
- **Clean Architecture**: Clear separation of concerns
- **SOLID Principles**: Single responsibility, open/closed design
- **Type Hints**: Complete type annotations for maintainability
- **Comprehensive Logging**: Structured logging with appropriate levels

### Security Practices
- **No Hardcoded Secrets**: All sensitive data externalized
- **Input Validation**: Comprehensive frame and payload validation
- **Error Information**: Security-conscious error message design
- **Resource Limits**: Bounded memory and connection usage

### Testing Standards
- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end protocol testing
- **Edge Cases**: Disconnection, timeout, and error scenarios
- **Coverage**: 80%+ code coverage requirement

## 📚 Usage Examples

### Basic Mission Execution
```bash
# Connect to production server with recording
python lightman.py production.server.com 8080 --record

# Test staging environment
python lightman.py staging.server.com 8080 --test
```

### Session Analysis
```bash
# Replay last mission
python lightman.py replay recordings/mission_20250917_124530.json

# Analyze specific session
python lightman.py replay recordings/session_debug_001.json
```

### TUI Navigation
```
N / n     - Next step in session
P / p     - Previous step in session  
Q / q     - Quit replay application
R / r     - Reload session file
H / h     - Toggle help display
```

## 🚨 Mission Critical Notes

1. **Server Lockdown**: Target servers may disconnect without warning - handle gracefully
2. **Protocol Compliance**: Strict adherence to nonce sequencing required
3. **Session Recording**: Always enable recording for mission auditing
4. **Override Codes**: Transmit retrieved codes to NORAD command immediately

## 🔧 Dependencies

- **Python 3.7+**: Core runtime requirement
- **Standard Library Only**: No external dependencies for core functionality
- **Optional**: `coverage` module for test coverage analysis

## 📝 License

Mission-critical software for LIGHTMAN operations. Educational use permitted.