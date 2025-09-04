# Discord Personal Data Bot

## Overview

This is a Discord bot designed for personal data management through Direct Messages (DMs). The bot automatically categorizes and stores various types of user data including passwords, emails, URLs, notes, and text extracted from images using OCR. It operates exclusively in DMs for privacy and security, providing users with a personal assistant for organizing and retrieving their information.

The bot features intelligent auto-detection of different data types, persistent storage, command-based interactions, and OCR capabilities for extracting text from uploaded images. It's designed to be deployed on platforms like Replit with keep-alive functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Bot Architecture
- **Discord.py Framework**: Built using discord.py library with command prefix system
- **DM-Only Operation**: Bot exclusively responds to Direct Messages, ignoring server messages
- **Modular Design**: Separated into distinct modules for storage, OCR, commands, configuration, and monitoring
- **Event-Driven**: Uses Discord's event system for message handling and auto-categorization

### Data Storage Layer
- **SQLite Database**: Uses aiosqlite for asynchronous database operations
- **User-Scoped Storage**: Data is isolated per Discord user ID
- **Auto-Categorization**: Intelligent detection and storage of passwords, emails, URLs, credentials, and notes
- **Data Validation**: Input sanitization and length validation for security
- **Persistent Storage**: All data persists across bot restarts

### OCR Processing
- **Tesseract Integration**: Uses pytesseract for optical character recognition
- **Asynchronous Processing**: OCR operations run in thread pool to avoid blocking
- **PIL Image Processing**: Handles various image formats for text extraction
- **Automatic Text Storage**: Extracted text is automatically categorized and stored

### Command System
- **Pattern Matching**: Regex-based detection for emails, URLs, and data patterns
- **Command Handler**: Centralized processing of user commands and triggers
- **CRUD Operations**: Create, read, update, delete operations for stored data
- **Search Functionality**: Full-text search across stored data categories

### Configuration Management
- **Environment Variables**: Configuration through environment variables for security
- **Validation System**: Startup validation for required configuration
- **Replit Compatibility**: Special configuration handling for Replit deployment
- **Logging Configuration**: Configurable logging levels and file output

### Monitoring and Health
- **Performance Monitoring**: Tracks messages processed, commands executed, and errors
- **Error Handling**: Centralized error logging and metrics collection
- **Keep-Alive Server**: Flask web server for Replit hosting to prevent sleeping
- **Health Endpoints**: HTTP endpoints for monitoring bot status and uptime

## External Dependencies

### Core Dependencies
- **Discord.py**: Discord API wrapper for bot functionality
- **aiosqlite**: Asynchronous SQLite database adapter
- **Flask**: Lightweight web server for keep-alive functionality

### OCR Dependencies
- **pytesseract**: Python wrapper for Tesseract OCR engine
- **Pillow (PIL)**: Image processing library for handling various image formats
- **opencv-python**: Advanced image processing capabilities (optional)

### Development and Testing
- **pytest**: Testing framework for unit and integration tests
- **pytest-asyncio**: Async testing support
- **aiofiles**: Asynchronous file operations

### Platform Integration
- **Replit Environment**: Special handling for Replit deployment and database
- **Environment Variables**: Secure configuration through environment variables
- **Tesseract OCR Engine**: External binary dependency for text extraction

### Security Considerations
- **Input Sanitization**: SQL injection prevention and content validation
- **Rate Limiting**: Protection against message spam and abuse
- **Data Encryption**: Optional encryption support for sensitive data
- **User Isolation**: Complete data separation between different users