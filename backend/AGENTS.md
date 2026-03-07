# AGENTS

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: `npx openskills read <skill-name>` (run in your shell)
  - For multiple: `npx openskills read skill-one,skill-two`
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>async-python-patterns</name>
<description>Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations.</description>
<location>project</location>
</skill>

<skill>
<name>cqrs-implementation</name>
<description>Implement Command Query Responsibility Segregation for scalable architectures. Use when separating read and write models, optimizing query performance, or building event-sourced systems.</description>
<location>project</location>
</skill>

<skill>
<name>database-migration</name>
<description>Execute database migrations across ORMs and platforms with zero-downtime strategies, data transformation, and rollback procedures. Use when migrating databases, changing schemas, performing data transformations, or implementing zero-downtime deployment strategies.</description>
<location>project</location>
</skill>

<skill>
<name>fastapi-templates</name>
<description>Create production-ready FastAPI projects with async patterns, dependency injection, and comprehensive error handling. Use when building new FastAPI applications or setting up backend API projects.</description>
<location>project</location>
</skill>

<skill>
<name>memory-safety-patterns</name>
<description>Implement memory-safe programming with RAII, ownership, smart pointers, and resource management across Rust, C++, and C. Use when writing safe systems code, managing resources, or preventing memory bugs.</description>
<location>project</location>
</skill>

<skill>
<name>postgresql</name>
<description>Design a PostgreSQL-specific schema. Covers best-practices, data types, indexing, constraints, performance patterns, and advanced features</description>
<location>project</location>
</skill>

<skill>
<name>python-anti-patterns</name>
<description>Common Python anti-patterns to avoid. Use as a checklist when reviewing code, before finalizing implementations, or when debugging issues that might stem from known bad practices.</description>
<location>project</location>
</skill>

<skill>
<name>python-background-jobs</name>
<description>Python background job patterns including task queues, workers, and event-driven architecture. Use when implementing async task processing, job queues, long-running operations, or decoupling work from request/response cycles.</description>
<location>project</location>
</skill>

<skill>
<name>python-code-style</name>
<description>Python code style, linting, formatting, naming conventions, and documentation standards. Use when writing new code, reviewing style, configuring linters, writing docstrings, or establishing project standards.</description>
<location>project</location>
</skill>

<skill>
<name>python-configuration</name>
<description>Python configuration management via environment variables and typed settings. Use when externalizing config, setting up pydantic-settings, managing secrets, or implementing environment-specific behavior.</description>
<location>project</location>
</skill>

<skill>
<name>python-design-patterns</name>
<description>Python design patterns including KISS, Separation of Concerns, Single Responsibility, and composition over inheritance. Use when making architecture decisions, refactoring code structure, or evaluating when abstractions are appropriate.</description>
<location>project</location>
</skill>

<skill>
<name>python-error-handling</name>
<description>Python error handling patterns including input validation, exception hierarchies, and partial failure handling. Use when implementing validation logic, designing exception strategies, handling batch processing failures, or building robust APIs.</description>
<location>project</location>
</skill>

<skill>
<name>python-observability</name>
<description>Python observability patterns including structured logging, metrics, and distributed tracing. Use when adding logging, implementing metrics collection, setting up tracing, or debugging production systems.</description>
<location>project</location>
</skill>

<skill>
<name>python-packaging</name>
<description>Create distributable Python packages with proper project structure, setup.py/pyproject.toml, and publishing to PyPI. Use when packaging Python libraries, creating CLI tools, or distributing Python code.</description>
<location>project</location>
</skill>

<skill>
<name>python-performance-optimization</name>
<description>Profile and optimize Python code using cProfile, memory profilers, and performance best practices. Use when debugging slow Python code, optimizing bottlenecks, or improving application performance.</description>
<location>project</location>
</skill>

<skill>
<name>python-project-structure</name>
<description>Python project organization, module architecture, and public API design. Use when setting up new projects, organizing modules, defining public interfaces with __all__, or planning directory layouts.</description>
<location>project</location>
</skill>

<skill>
<name>python-resilience</name>
<description>Python resilience patterns including automatic retries, exponential backoff, timeouts, and fault-tolerant decorators. Use when adding retry logic, implementing timeouts, building fault-tolerant services, or handling transient failures.</description>
<location>project</location>
</skill>

<skill>
<name>python-resource-management</name>
<description>Python resource management with context managers, cleanup patterns, and streaming. Use when managing connections, file handles, implementing cleanup logic, or building streaming responses with accumulated state.</description>
<location>project</location>
</skill>

<skill>
<name>python-testing-patterns</name>
<description>Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices.</description>
<location>project</location>
</skill>

<skill>
<name>python-type-safety</name>
<description>Python type safety with type hints, generics, protocols, and strict type checking. Use when adding type annotations, implementing generic classes, defining structural interfaces, or configuring mypy/pyright.</description>
<location>project</location>
</skill>

<skill>
<name>sql-optimization-patterns</name>
<description>Master SQL query optimization, indexing strategies, and EXPLAIN analysis to dramatically improve database performance and eliminate slow queries. Use when debugging slow queries, designing database schemas, or optimizing application performance.</description>
<location>project</location>
</skill>

<skill>
<name>temporal-python-testing</name>
<description>Test Temporal workflows with pytest, time-skipping, and mocking strategies. Covers unit testing, integration testing, replay testing, and local development setup. Use when implementing Temporal workflow tests or debugging test failures.</description>
<location>project</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
