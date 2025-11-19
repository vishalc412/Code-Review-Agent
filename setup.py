from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="code-review-agents",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered code review agents for Azure DevOps, GitLab, and GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-review-agents",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.0.0",
        "azure-devops>=7.0.0",
        "python-gitlab>=4.4.0",
        "PyGithub>=2.1.1",
        "anthropic>=0.40.0",
        "openai>=1.12.0",
        "GitPython>=3.1.40",
        "unidiff>=0.7.5",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
        "structlog>=23.2.0",
        "python-json-logger>=2.0.7",
    ],
    entry_points={
        "console_scripts": [
            "review-agent=agents.review_agent:main",
            "fix-agent=agents.fix_agent:main",
        ],
    },
)
