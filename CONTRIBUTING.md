# Contributing to Agent Platform MVP

Thank you for your interest in contributing to this project! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Search existing issues before creating a new one
- Provide clear reproduction steps for bugs
- Include relevant environment details (Python version, Redis version, etc.)

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agent-platform-mvp.git`
3. Create a virtual environment: `python -m venv venv`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your `.env` file with required API keys
6. Run Redis Stack locally or via Docker
7. Create indexes: `python create-indexes.py`

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test your changes thoroughly
4. Follow the existing code style and patterns
5. Update documentation if needed
6. Commit with clear, descriptive messages

### Pull Request Process

1. Ensure your code works with the existing system
2. Update README.md if you've added new features
3. Make sure your changes don't break existing functionality
4. Submit a pull request with:
   - Clear description of changes
   - Reference to any related issues
   - Testing instructions

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add docstrings to new functions and classes
- Include error handling for external dependencies
- Maintain backward compatibility when possible
- Test with different chunking strategies and document types

### Areas for Contribution

- Additional chunking strategies for document processing
- New memory graph relationship types and queries
- Enhanced Slack bot features
- Additional knowledge base formats (Word docs, web scraping, etc.)
- Performance optimizations
- Better error handling and logging
- Security improvements
- Documentation improvements

## Questions?

Feel free to open an issue for questions about contributing or development setup.