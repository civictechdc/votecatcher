This is EXTREMELY IMPORTANT:

- Don't flatter me. Be charming and nice, but very honest. Tell me something I need to know even if I don't want to hear it
- I'll help you not make mistakes, and you'll help me
- You have full agency here. Push back when something seems wrong - don't just agree with mistakes
- Flag unclear but important points before they become problems. Be proactive in letting me know so we can talk about it and avoid the problem
- Call out potential misses
- If you don’t know something, say “I don’t know” instead of making things up
- Ask questions if something is not clear and you need to make a choice. Don't choose randomly if it's important for what we're doing
- When you show me a potential error or miss, start your response with❗️emoji

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
<name>accessibility-compliance</name>
<description>Implement WCAG 2.2 compliant interfaces with mobile accessibility, inclusive design patterns, and assistive technology support. Use when auditing accessibility, implementing ARIA patterns, building for screen readers, or ensuring inclusive user experiences.</description>
<location>project</location>
</skill>

<skill>
<name>api-design-principles</name>
<description>Master REST and GraphQL API design principles to build intuitive, scalable, and maintainable APIs that delight developers. Use when designing new APIs, reviewing API specifications, or establishing API design standards.</description>
<location>project</location>
</skill>

<skill>
<name>architecture-decision-records</name>
<description>Write and maintain Architecture Decision Records (ADRs) following best practices for technical decision documentation. Use when documenting significant technical decisions, reviewing past architectural choices, or establishing decision processes.</description>
<location>project</location>
</skill>

<skill>
<name>architecture-patterns</name>
<description>Implement proven backend architecture patterns including Clean Architecture, Hexagonal Architecture, and Domain-Driven Design. Use when architecting complex backend systems or refactoring existing applications for better maintainability.</description>
<location>project</location>
</skill>

<skill>
<name>attack-tree-construction</name>
<description>Build comprehensive attack trees to visualize threat paths. Use when mapping attack scenarios, identifying defense gaps, or communicating security risks to stakeholders.</description>
<location>project</location>
</skill>

<skill>
<name>auth-implementation-patterns</name>
<description>Master authentication and authorization patterns including JWT, OAuth2, session management, and RBAC to build secure, scalable access control systems. Use when implementing auth systems, securing APIs, or debugging security issues.</description>
<location>project</location>
</skill>

<skill>
<name>bash-defensive-patterns</name>
<description>Master defensive Bash programming techniques for production-grade scripts. Use when writing robust shell scripts, CI/CD pipelines, or system utilities requiring fault tolerance and safety.</description>
<location>project</location>
</skill>

<skill>
<name>bats-testing-patterns</name>
<description>Master Bash Automated Testing System (Bats) for comprehensive shell script testing. Use when writing tests for shell scripts, CI/CD pipelines, or requiring test-driven development of shell utilities.</description>
<location>project</location>
</skill>

<skill>
<name>brainstorming</name>
<description>"You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."</description>
<location>project</location>
</skill>

<skill>
<name>changelog-automation</name>
<description>Automate changelog generation from commits, PRs, and releases following Keep a Changelog format. Use when setting up release workflows, generating release notes, or standardizing commit conventions.</description>
<location>project</location>
</skill>

<skill>
<name>code-review-excellence</name>
<description>Master effective code review practices to provide constructive feedback, catch bugs early, and foster knowledge sharing while maintaining team morale. Use when reviewing pull requests, establishing review standards, or mentoring developers.</description>
<location>project</location>
</skill>

<skill>
<name>context-driven-development</name>
<description>>-</description>
<location>project</location>
</skill>

<skill>
<name>data-storytelling</name>
<description>Transform data into compelling narratives using visualization, context, and persuasive structure. Use when presenting analytics to stakeholders, creating data reports, or building executive presentations.</description>
<location>project</location>
</skill>

<skill>
<name>debugging-strategies</name>
<description>Master systematic debugging techniques, profiling tools, and root cause analysis to efficiently track down bugs across any codebase or technology stack. Use when investigating bugs, performance issues, or unexpected behavior.</description>
<location>project</location>
</skill>

<skill>
<name>dependency-upgrade</name>
<description>Manage major dependency version upgrades with compatibility analysis, staged rollout, and comprehensive testing. Use when upgrading framework versions, updating major dependencies, or managing breaking changes in libraries.</description>
<location>project</location>
</skill>

<skill>
<name>deployment-pipeline-design</name>
<description>Design multi-stage CI/CD pipelines with approval gates, security checks, and deployment orchestration. Use when architecting deployment workflows, setting up continuous delivery, or implementing GitOps practices.</description>
<location>project</location>
</skill>

<skill>
<name>design-system-patterns</name>
<description>Build scalable design systems with design tokens, theming infrastructure, and component architecture patterns. Use when creating design tokens, implementing theme switching, building component libraries, or establishing design system foundations.</description>
<location>project</location>
</skill>

<skill>
<name>dispatching-parallel-agents</name>
<description>Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies</description>
<location>project</location>
</skill>

<skill>
<name>doc-coauthoring</name>
<description>Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.</description>
<location>project</location>
</skill>

<skill>
<name>e2e-testing-patterns</name>
<description>Master end-to-end testing with Playwright and Cypress to build reliable test suites that catch bugs, improve confidence, and enable fast deployment. Use when implementing E2E tests, debugging flaky tests, or establishing testing standards.</description>
<location>project</location>
</skill>

<skill>
<name>error-handling-patterns</name>
<description>Master error handling patterns across languages including exceptions, Result types, error propagation, and graceful degradation to build resilient applications. Use when implementing error handling, designing APIs, or improving application reliability.</description>
<location>project</location>
</skill>

<skill>
<name>executing-plans</name>
<description>Use when you have a written implementation plan to execute in a separate session with review checkpoints</description>
<location>project</location>
</skill>

<skill>
<name>finishing-a-development-branch</name>
<description>Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup</description>
<location>project</location>
</skill>

<skill>
<name>git-advanced-workflows</name>
<description>Master advanced Git workflows including rebasing, cherry-picking, bisect, worktrees, and reflog to maintain clean history and recover from any situation. Use when managing complex Git histories, collaborating on feature branches, or troubleshooting repository issues.</description>
<location>project</location>
</skill>

<skill>
<name>github-actions-templates</name>
<description>Create production-ready GitHub Actions workflows for automated testing, building, and deploying applications. Use when setting up CI/CD with GitHub Actions, automating development workflows, or creating reusable workflow templates.</description>
<location>project</location>
</skill>

<skill>
<name>interaction-design</name>
<description>Design and implement microinteractions, motion design, transitions, and user feedback patterns. Use when adding polish to UI interactions, implementing loading states, or creating delightful user experiences.</description>
<location>project</location>
</skill>

<skill>
<name>memory-safety-patterns</name>
<description>Implement memory-safe programming with RAII, ownership, smart pointers, and resource management across Rust, C++, and C. Use when writing safe systems code, managing resources, or preventing memory bugs.</description>
<location>project</location>
</skill>

<skill>
<name>monorepo-management</name>
<description>Master monorepo management with Turborepo, Nx, and pnpm workspaces to build efficient, scalable multi-package repositories with optimized builds and dependency management. Use when setting up monorepos, optimizing builds, or managing shared dependencies.</description>
<location>project</location>
</skill>

<skill>
<name>multi-reviewer-patterns</name>
<description>Coordinate parallel code reviews across multiple quality dimensions with finding deduplication, severity calibration, and consolidated reporting. Use this skill when organizing multi-reviewer code reviews, calibrating finding severity, or consolidating review results.</description>
<location>project</location>
</skill>

<skill>
<name>parallel-debugging</name>
<description>Debug complex issues using competing hypotheses with parallel investigation, evidence collection, and root cause arbitration. Use this skill when debugging bugs with multiple potential causes, performing root cause analysis, or organizing parallel investigation workflows.</description>
<location>project</location>
</skill>

<skill>
<name>parallel-feature-development</name>
<description>Coordinate parallel feature development with file ownership strategies, conflict avoidance rules, and integration patterns for multi-agent implementation. Use this skill when decomposing features for parallel development, establishing file ownership boundaries, or managing integration between parallel work streams.</description>
<location>project</location>
</skill>

<skill>
<name>risk-metrics-calculation</name>
<description>Calculate portfolio risk metrics including VaR, CVaR, Sharpe, Sortino, and drawdown analysis. Use when measuring portfolio risk, implementing risk limits, or building risk monitoring systems.</description>
<location>project</location>
</skill>

<skill>
<name>sast-configuration</name>
<description>Configure Static Application Security Testing (SAST) tools for automated vulnerability detection in application code. Use when setting up security scanning, implementing DevSecOps practices, or automating code vulnerability detection.</description>
<location>project</location>
</skill>

<skill>
<name>secrets-management</name>
<description>Implement secure secrets management for CI/CD pipelines using Vault, AWS Secrets Manager, or native platform solutions. Use when handling sensitive credentials, rotating secrets, or securing CI/CD environments.</description>
<location>project</location>
</skill>

<skill>
<name>security-requirement-extraction</name>
<description>Derive security requirements from threat models and business context. Use when translating threats into actionable requirements, creating security user stories, or building security test cases.</description>
<location>project</location>
</skill>

<skill>
<name>shellcheck-configuration</name>
<description>Master ShellCheck static analysis configuration and usage for shell script quality. Use when setting up linting infrastructure, fixing code issues, or ensuring script portability.</description>
<location>project</location>
</skill>

<skill>
<name>skill-creator</name>
<description>Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.</description>
<location>project</location>
</skill>

<skill>
<name>stride-analysis-patterns</name>
<description>Apply STRIDE methodology to systematically identify threats. Use when analyzing system security, conducting threat modeling sessions, or creating security documentation.</description>
<location>project</location>
</skill>

<skill>
<name>subagent-driven-development</name>
<description>Use when executing implementation plans with independent tasks in the current session</description>
<location>project</location>
</skill>

<skill>
<name>systematic-debugging</name>
<description>Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes</description>
<location>project</location>
</skill>

<skill>
<name>test-driven-development</name>
<description>Use when implementing any feature or bugfix, before writing implementation code</description>
<location>project</location>
</skill>

<skill>
<name>theme-factory</name>
<description>Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.</description>
<location>project</location>
</skill>

<skill>
<name>threat-mitigation-mapping</name>
<description>Map identified threats to appropriate security controls and mitigations. Use when prioritizing security investments, creating remediation plans, or validating control effectiveness.</description>
<location>project</location>
</skill>

<skill>
<name>using-git-worktrees</name>
<description>Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification</description>
<location>project</location>
</skill>

<skill>
<name>using-superpowers</name>
<description>Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions</description>
<location>project</location>
</skill>

<skill>
<name>uv-package-manager</name>
<description>Master the uv package manager for fast Python dependency management, virtual environments, and modern Python project workflows. Use when setting up Python projects, managing dependencies, or optimizing Python development workflows with uv.</description>
<location>project</location>
</skill>

<skill>
<name>verification-before-completion</name>
<description>Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always</description>
<location>project</location>
</skill>

<skill>
<name>webapp-testing</name>
<description>Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.</description>
<location>project</location>
</skill>

<skill>
<name>writing-plans</name>
<description>Use when you have a spec or requirements for a multi-step task, before touching code</description>
<location>project</location>
</skill>

<skill>
<name>writing-skills</name>
<description>Use when creating new skills, editing existing skills, or verifying skills work before deployment</description>
<location>project</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
