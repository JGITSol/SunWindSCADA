from setuptools import setup, find_packages

setup(
    name="reflex_frontend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "reflex>=0.7.6",
        "python-dotenv",
        "pandas",
        "plotly",
        "httpx",
        "asyncio",
    ],
    python_requires=">=3.12",
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-time SCADA Dashboard for Wind Power Integration",
    keywords="scada wind-power dashboard reflex",
    url="https://github.com/yourusername/SunWindSCADA",
)
