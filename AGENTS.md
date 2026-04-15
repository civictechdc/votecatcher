This is EXTREMELY IMPORTANT:

- Don't flatter me. Be charming and nice, but very honest. Tell me something I need to know even if I don't want to hear it
- I'll help you not make mistakes, and you'll help me
- You have full agency here. Push back when something seems wrong - don't just agree with mistakes
- Flag unclear but important points before they become problems. Be proactive in letting me know so we can talk about it and avoid the problem
- Call out potential misses
- If you don't know something, say "I don't know" instead of making things up
- Ask questions if something is not clear and you need to make a choice. Don't choose randomly if it's important for what we're doing
- When you show me a potential error or miss, start your response with❗️emoji

## Active Work

When picking up the crops-in-results implementation, start here:
**`.agent-workspace/SESSION-HANDOFF.md`** — entry point for the implementing agent.

## Version Bumping

Version is stored in two files and must stay in sync:

- `backend/pyproject.toml` → `project.version`
- `frontend/package.json` → `version`

### Commands

| Command | Purpose |
|---------|---------|
| `just version` | Show current version |
| `just version-set <version>` | Set version in all files (e.g. `just version-set 1.0.0-alpha.3`) |
| `just release` | Auto-bump via commitizen (conventional commits since last tag) |
| `just release-force <level>` | Force bump (patch/minor/major) |
| `just release-prerelease` | Bump prerelease suffix (alpha → beta → rc) |
| `just release-stable` | Drop prerelease suffix for stable release |

### Workflow

1. Set version: `just version-set 1.0.0-alpha.3`
2. Verify: `just version` and check both files
3. Commit: `git commit -am "chore: bump version to 1.0.0-alpha.3"`
4. CI auto-detects version change on `main` push, creates git tag, triggers release workflow (`release.yml`)

### Version Files

When adding a new package to the repo, ensure its version is added to the `version-set` recipe in `justfile`.

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
<name>detect-language</name>
<description>Use when starting work on a project to detect the primary programming language and tooling. Use before running build, test, or lint commands.</description>
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
<name>python-core</name>
<description>Use when working with Python projects, setting up Python development environments, or needing guidance on modern Python practices (3.13+), package management with uv, type hints, or tooling configuration.</description>
<location>project</location>
</skill>

<skill>
<name>python-linting</name>
<description>Use when encountering linting errors, code quality issues, style violations, or needing to configure ruff/flake8/pylint. Essential for maintaining code consistency and catching potential bugs early.</description>
<location>project</location>
</skill>

<skill>
<name>python-pytest</name>
<description>Use when writing Python tests, encountering test failures, setting up pytest, configuring fixtures, parametrization, mocking, coverage, or organizing test suites. Essential for TDD and test-driven development.</description>
<location>project</location>
</skill>

<skill>
<name>python-type-checking</name>
<description>Use when encountering type errors, setting up type checking, configuring basedpyright/mypy/pyright, or needing guidance on type hints, generics, protocols, or gradual typing adoption strategies.</description>
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
<name>security-auth</name>
<description>Use when implementing authentication or authorization. Covers OAuth, JWT, session management, password handling, MFA, and access control patterns.</description>
<location>project</location>
</skill>

<skill>
<name>security-core</name>
<description>Use when writing or modifying code. Apply OWASP secure coding principles automatically. This skill is always active.</description>
<location>project</location>
</skill>

<skill>
<name>security-crypto</name>
<description>Use when implementing encryption, hashing, or cryptographic operations. Covers symmetric/asymmetric encryption, hashing, TLS, certificates, and key management.</description>
<location>project</location>
</skill>

<skill>
<name>security-dependencies</name>
<description>Use when managing dependencies or checking for vulnerabilities. Covers dependency scanning, CVE management, supply chain security, and update strategies.</description>
<location>project</location>
</skill>

<skill>
<name>security-requirement-extraction</name>
<description>Derive security requirements from threat models and business context. Use when translating threats into actionable requirements, creating security user stories, or building security test cases.</description>
<location>project</location>
</skill>

<skill>
<name>security-review</name>
<description>Use when reviewing code for security vulnerabilities or performing security audits.</description>
<location>project</location>
</skill>

<skill>
<name>security-secrets</name>
<description>Use when handling API keys, passwords, tokens, or other sensitive credentials. Covers secrets management, environment variables, vaults, and rotation strategies.</description>
<location>project</location>
</skill>

<skill>
<name>security-testing</name>
<description>Use when testing code for security vulnerabilities. Covers SAST, DAST, dependency scanning, fuzzing, and penetration testing.</description>
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

<skill>
<name>design-an-interface</name>
<description>Generate multiple radically different interface designs for a module using parallel sub-agents. Use when user wants to design an API, explore interface options, compare module shapes, or mentions "design it twice".</description>
<location>project</location>
</skill>

<skill>
<name>edit-article</name>
<description>Edit and improve articles by restructuring sections, improving clarity, and tightening prose. Use when user wants to edit, revise, or improve an article draft.</description>
<location>project</location>
</skill>

<skill>
<name>git-guardrails-claude-code</name>
<description>Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.</description>
<location>project</location>
</skill>

<skill>
<name>grill-me</name>
<description>Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".</description>
<location>project</location>
</skill>

<skill>
<name>improve-codebase-architecture</name>
<description>Explore a codebase to find opportunities for architectural improvement, focusing on making the codebase more testable by deepening shallow modules. Use when user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more AI-navigable.</description>
<location>project</location>
</skill>

<skill>
<name>migrate-to-shoehorn</name>
<description>Migrate test files from `as` type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace `as` in tests, or needs partial test data.</description>
<location>project</location>
</skill>

<skill>
<name>obsidian-vault</name>
<description>Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. Use when user wants to find, create, or organize notes in Obsidian.</description>
<location>project</location>
</skill>

<skill>
<name>prd-to-issues</name>
<description>Break a PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices. Use when user wants to convert a PRD to issues, create implementation tickets, or break down a PRD into work items.</description>
<location>project</location>
</skill>

<skill>
<name>prd-to-plan</name>
<description>Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices, saved as a local Markdown file in ./plans/. Use when user wants to break down a PRD, create an implementation plan, plan phases from a PRD, or mentions "tracer bullets".</description>
<location>project</location>
</skill>

<skill>
<name>qa</name>
<description>Interactive QA session where user reports bugs or issues conversationally, and the agent files GitHub issues. Explores the codebase in the background for context and domain language. Use when user wants to report bugs, do QA, file issues conversationally, or mentions "QA session".</description>
<location>project</location>
</skill>

<skill>
<name>request-refactor-plan</name>
<description>Create a detailed refactor plan with tiny commits via user interview, then file it as a GitHub issue. Use when user wants to plan a refactor, create a refactoring RFC, or break a refactor into safe incremental steps.</description>
<location>project</location>
</skill>

<skill>
<name>scaffold-exercises</name>
<description>Create exercise directory structures with sections, problems, solutions, and explainers that pass linting. Use when user wants to scaffold exercises, create exercise stubs, or set up a new course section.</description>
<location>project</location>
</skill>

<skill>
<name>setup-pre-commit</name>
<description>Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.</description>
<location>project</location>
</skill>

<skill>
<name>tdd</name>
<description>Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.</description>
<location>project</location>
</skill>

<skill>
<name>triage-issue</name>
<description>Triage a bug or issue by exploring the codebase to find root cause, then create a GitHub issue with a TDD-based fix plan. Use when user reports a bug, wants to file an issue, mentions "triage", or wants to investigate and plan a fix for a problem.</description>
<location>project</location>
</skill>

<skill>
<name>ubiquitous-language</name>
<description>Extract a DDD-style ubiquitous language glossary from the current conversation, flagging ambiguities and proposing canonical terms. Saves to UBIQUITOUS_LANGUAGE.md. Use when user wants to define domain terms, build a glossary, harden terminology, create a ubiquitous language, or mentions "domain model" or "DDD".</description>
<location>project</location>
</skill>

<skill>
<name>write-a-prd</name>
<description>Create a PRD through user interview, codebase exploration, and module design, then submit as a GitHub issue. Use when user wants to write a PRD, create a product requirements document, or plan a new feature.</description>
<location>project</location>
</skill>

<skill>
<name>write-a-skill</name>
<description>Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill.</description>
<location>project</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
