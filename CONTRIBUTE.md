# Contribution by @yunustechin

This document outlines my contributions to the **nyt-downloader** project, focusing on enhancing its structure, maintainability, performance, and testability.

I began by modernizing the dependency management system, replacing the traditional ```requirements.txt``` file with a ```pyproject.toml``` setup. This aligns the project with **PEP 518** standards, improving compatibility and streamlining dependency management for long-term maintenance.

Next, I conducted a comprehensive refactoring of the main project files. The original ```nyt_downloader.py``` and ```settingsWindow.py``` were reorganized into a modular, well-structured architecture with clear separation of concerns:

- **```core/```** – Contains essential logic, including:
  - ```downloader.py```: Core download functionality
  - ```logger.py```: Centralized logging system
  - ```queue.py```: Asynchronous task queue for downloads
  - ```settings.py```: User and application settings management
- **```ui/```** – Manages all user interface elements:
  - ```main_window.py```: Main application window
  - ```widgets.py```: Reusable UI components
- **```utils/```** – General-purpose helper functions:
  - ```helpers.py```
- **```app.py```** – Application entry point

To enhance code quality, I improved readability by adopting meaningful and consistent naming conventions for functions, classes, and variables. I also added comprehensive inline documentation, making the codebase more accessible and easier to navigate for future contributors. Additionally, I introduced **type hints** using Python's ```typing``` module to improve code clarity, enforce type safety, and facilitate better IDE support and code maintenance.

To ensure the project is test-ready, I structured the codebase to support unit testing. The modular design and clear separation of concerns make it easier to write and run tests for individual components, improving reliability and enabling future enhancements with confidence.

A significant technical improvement is the implementation of **asynchronous downloading** through the new ```queue.py``` module. This enables concurrent processing of multiple downloads, greatly enhancing performance and user experience.

Overall, these changes modernize the **nyt-downloader** project, making it more scalable, testable, and collaborative. I’m excited to contribute to its growth and maintainability.

Thanks for reading – happy coding!  
**– @yunustechin**